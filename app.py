"""
PDF to Handwriting Converter
Main Flask Application
"""
import os
import sys
import uuid
import logging
import traceback
import io
import zipfile
from pathlib import Path
from flask import (Flask, request, jsonify, send_file, 
                   render_template, make_response)
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ─── App Setup ──────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

app.config.update(
    MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB
    SECRET_KEY=os.environ.get('SECRET_KEY', os.urandom(32).hex()),
    JSON_SORT_KEYS=False,
)

# ─── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
UPLOAD_DIR  = Path(tempfile.gettempdir()) / 'phc_uploads'
OUTPUT_DIR  = Path(tempfile.gettempdir()) / 'phc_outputs'
FONTS_DIR   = BASE_DIR / 'static' / 'fonts'

for d in (UPLOAD_DIR, OUTPUT_DIR, FONTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

ALLOWED_EXT = {'pdf', 'jpg', 'jpeg', 'png'}

# ─── Helpers ────────────────────────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def make_session_id() -> str:
    return str(uuid.uuid4()).replace('-', '')[:16]

# ─── Routes ─────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check for Render"""
    return jsonify({'status': 'ok', 'version': '2.0'}), 200


@app.route('/api/fonts')
def api_fonts():
    """List available handwriting fonts"""
    try:
        from utils.font_manager import FontManager
        fm = FontManager(FONTS_DIR)
        fonts = fm.get_available_fonts()
        return jsonify({'status': 'success', 'fonts': fonts})
    except Exception as e:
        logger.error(f"Font list error: {e}")
        return jsonify({'status': 'error', 'fonts': [], 'error': str(e)}), 500


@app.route('/api/fonts/download', methods=['POST'])
def api_download_fonts():
    """Trigger background font download"""
    try:
        from utils.font_manager import FontManager
        fm = FontManager(FONTS_DIR)
        count = fm.ensure_fonts_downloaded()
        return jsonify({'status': 'success', 'downloaded': count})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500


@app.route('/api/extract', methods=['POST'])
def api_extract():
    """Extract text from file upload or direct text"""
    try:
        input_type = request.form.get('input_type', 'file')

        # ── Direct text ──────────────────────────────────────────────────
        if input_type == 'text':
            text = request.form.get('text', '').strip()
            if not text:
                return jsonify({'error': 'No text provided'}), 400
            return jsonify({
                'status': 'success',
                'text': text,
                'pages': [text],
                'page_count': 1,
                'layout_data': None,
            })

        # ── File upload ──────────────────────────────────────────────────
        if 'file' not in request.files:
            return jsonify({'error': 'No file in request'}), 400

        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'error': 'Empty file'}), 400

        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Unsupported file type. '
                         'Upload PDF, JPG, or PNG only.'
            }), 400

        # Save temporarily
        ext      = file.filename.rsplit('.', 1)[1].lower()
        sid      = make_session_id()
        tmp_path = UPLOAD_DIR / f"{sid}.{ext}"
        file.save(str(tmp_path))

        try:
            if ext == 'pdf':
                from utils.pdf_extractor import PDFExtractor
                result = PDFExtractor().extract(str(tmp_path))
            else:
                from utils.ocr_extractor import OCRExtractor
                result = OCRExtractor().extract(str(tmp_path))
        finally:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass

        return jsonify({
            'status': 'success',
            'text':        result.get('full_text', ''),
            'pages':       result.get('pages', []),
            'page_count':  result.get('page_count', 1),
            'layout_data': result.get('layout_data'),
        })

    except Exception as e:
        logger.error(f"Extract error:\n{traceback.format_exc()}")
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500


@app.route('/api/convert', methods=['POST'])
def api_convert():
    """Convert text/pages to handwritten output"""
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({'error': 'No JSON body'}), 400

        # Resolve pages list
        raw_pages = data.get('pages', [])
        raw_text  = data.get('text', '').strip()
        if not raw_pages:
            raw_pages = [raw_text] if raw_text else []

        pages = [p.strip() for p in raw_pages if str(p).strip()]
        if not pages:
            return jsonify({'error': 'No text content to convert'}), 400

        settings = {
            'font_name':    data.get('font_name', 'Kalam'),
            'font_size':    max(12, min(72, int(data.get('font_size', 28)))),
            'line_spacing': max(1.0, min(4.0, float(data.get('line_spacing', 1.8)))),
            'ink_color':    data.get('ink_color', 'blue'),
            'margin':       max(20, min(200, int(data.get('margin', 60)))),
            'paper_style':  data.get('paper_style', 'ruled'),
            'output_format': data.get('output_format', 'pdf'),
            'page_width':   int(data.get('page_width', 794)),
            'page_height':  int(data.get('page_height', 1123)),
            'preserve_layout': bool(data.get('preserve_layout', False)),
            'layout_data':  data.get('layout_data'),
        }

        # Ensure fonts exist (download if missing)
        from utils.font_manager import FontManager
        FontManager(FONTS_DIR).ensure_fonts_downloaded()

        from utils.handwriting_generator import HandwritingGenerator
        gen = HandwritingGenerator(FONTS_DIR, OUTPUT_DIR)

        sid    = make_session_id()
        fmt    = settings['output_format']
        result = {'status': 'success', 'session_id': sid,
                  'output_format': fmt}

        # Use layout-aware generator for PDFs when requested
        if (settings['preserve_layout'] and
                settings['layout_data'] and
                fmt in ('pdf', 'both')):
            from utils.handwriting_generator import PositionAwareGenerator
            pag = PositionAwareGenerator(FONTS_DIR, OUTPUT_DIR)
            pag.render_with_layout(settings['layout_data'], settings, sid)
        else:
            if fmt in ('pdf', 'both'):
                gen.generate_pdf(pages, settings, sid)
            if fmt in ('jpg', 'both'):
                gen.generate_jpg(pages, settings, sid)

        page_count = len(pages)
        result['page_count'] = page_count

        if fmt in ('pdf', 'both'):
            result['pdf_url']     = f'/api/download/{sid}/pdf'
            result['preview_url'] = f'/api/preview/{sid}'

        if fmt in ('jpg', 'both'):
            jpg_urls = [f'/api/download/{sid}/jpg/{i}'
                        for i in range(page_count)]
            result['jpg_urls']    = jpg_urls
            result['preview_url'] = jpg_urls[0] if jpg_urls else ''

        return jsonify(result)

    except Exception as e:
        logger.error(f"Convert error:\n{traceback.format_exc()}")
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500


@app.route('/api/preview/<sid>')
def api_preview(sid: str):
    """Return first-page PNG preview of a generated PDF"""
    # Sanitize
    sid = ''.join(c for c in sid if c.isalnum())
    pdf_path = OUTPUT_DIR / f"{sid}.pdf"
    png_path = OUTPUT_DIR / f"{sid}_preview.png"

    if not pdf_path.exists():
        return jsonify({'error': 'Session not found'}), 404

    try:
        if not png_path.exists():
            import fitz
            doc  = fitz.open(str(pdf_path))
            page = doc[0]
            mat  = fitz.Matrix(1.5, 1.5)
            pix  = page.get_pixmap(matrix=mat)
            pix.save(str(png_path))
            doc.close()

        return send_file(str(png_path), mimetype='image/png',
                         max_age=300)
    except Exception as e:
        logger.error(f"Preview error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<sid>/pdf')
def download_pdf(sid: str):
    sid      = ''.join(c for c in sid if c.isalnum())
    pdf_path = OUTPUT_DIR / f"{sid}.pdf"
    if not pdf_path.exists():
        return jsonify({'error': 'File not found – please convert again'}), 404
    return send_file(str(pdf_path), as_attachment=True,
                     download_name='handwritten_notes.pdf',
                     mimetype='application/pdf')


@app.route('/api/download/<sid>/jpg/<int:page>')
def download_jpg(sid: str, page: int):
    sid = ''.join(c for c in sid if c.isalnum())
    for ext in ('jpg', 'jpeg', 'png'):
        p = OUTPUT_DIR / f"{sid}_page_{page}.{ext}"
        if p.exists():
            return send_file(str(p), as_attachment=True,
                             download_name=f'handwritten_page_{page+1}.jpg',
                             mimetype='image/jpeg')
    return jsonify({'error': 'Page not found'}), 404


@app.route('/api/download/<sid>/all')
def download_all(sid: str):
    """ZIP of all JPG pages"""
    sid   = ''.join(c for c in sid if c.isalnum())
    files = sorted(OUTPUT_DIR.glob(f"{sid}_page_*.jpg")) + \
            sorted(OUTPUT_DIR.glob(f"{sid}_page_*.png"))

    if not files:
        return jsonify({'error': 'No pages found'}), 404

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, f in enumerate(files):
            zf.write(str(f), f'handwritten_page_{i+1}.jpg')
    buf.seek(0)

    return send_file(buf, as_attachment=True,
                     download_name='handwritten_notes.zip',
                     mimetype='application/zip')


# ─── Error Handlers ─────────────────────────────────────────────────────────

@app.errorhandler(413)
def too_large(_):
    return jsonify({'error': 'File too large (max 50 MB)'}), 413


@app.errorhandler(404)
def not_found(_):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('index.html')


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# ─── Startup ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Pre-download fonts
    try:
        from utils.font_manager import FontManager
        fm = FontManager(FONTS_DIR)
        fm.ensure_fonts_downloaded()
    except Exception as e:
        logger.warning(f"Startup font warning (non-fatal): {e}")

    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
