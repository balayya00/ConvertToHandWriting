"""
PDF to Handwriting Converter  –  app.py  v3.0
"""
import io, os, sys, uuid, logging, traceback, zipfile
from pathlib import Path
import tempfile

from flask import (Flask, request, jsonify, send_file,
                   render_template, make_response)
from flask_cors import CORS
from werkzeug.utils import secure_filename

# ── Logging ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

# ── App ────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)
app.config.update(
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024,
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24).hex()),
    JSON_SORT_KEYS = False,
)

BASE_DIR   = Path(__file__).parent
UPLOAD_DIR = Path(tempfile.gettempdir()) / 'phc_up'
OUTPUT_DIR = Path(tempfile.gettempdir()) / 'phc_out'
FONTS_DIR  = BASE_DIR / 'static' / 'fonts'
for d in (UPLOAD_DIR, OUTPUT_DIR, FONTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

ALLOWED = {'pdf','jpg','jpeg','png'}

def _sid():  return uuid.uuid4().hex[:16]
def _ok(f):  return '.' in f and f.rsplit('.',1)[1].lower() in ALLOWED
def _clean(s): return ''.join(c for c in s if c.isalnum())

# ── Routes ─────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    return jsonify(status='ok', version='3.0')

@app.route('/api/fonts')
def api_fonts():
    try:
        from utils.font_manager import FontManager
        fonts = FontManager(FONTS_DIR).get_available_fonts()
        return jsonify(status='success', fonts=fonts)
    except Exception as e:
        log.error(f"fonts: {e}")
        return jsonify(status='error', fonts=[], error=str(e))

@app.route('/api/extract', methods=['POST'])
def api_extract():
    try:
        itype = request.form.get('input_type', 'file')

        if itype == 'text':
            txt = request.form.get('text','').strip()
            if not txt:
                return jsonify(error='No text provided'), 400
            return jsonify(status='success', text=txt,
                           pages=[txt], page_count=1, layout_data=None)

        if 'file' not in request.files:
            return jsonify(error='No file uploaded'), 400
        f = request.files['file']
        if not f or not f.filename:
            return jsonify(error='Empty file'), 400
        if not _ok(f.filename):
            return jsonify(error='Unsupported type. Upload PDF, JPG or PNG'), 400

        ext  = f.filename.rsplit('.',1)[1].lower()
        sid  = _sid()
        tmp  = UPLOAD_DIR / f"{sid}.{ext}"
        f.save(str(tmp))

        try:
            if ext == 'pdf':
                from utils.pdf_extractor import PDFExtractor
                res = PDFExtractor().extract(str(tmp))
            else:
                from utils.ocr_extractor import OCRExtractor
                res = OCRExtractor().extract(str(tmp))
        finally:
            tmp.unlink(missing_ok=True)

        return jsonify(
            status      = 'success',
            text        = res.get('full_text',''),
            pages       = res.get('pages',[]),
            page_count  = res.get('page_count',1),
            layout_data = res.get('layout_data'),
        )

    except Exception as e:
        log.error(traceback.format_exc())
        return jsonify(error=f'Extraction failed: {e}'), 500


@app.route('/api/convert', methods=['POST'])
def api_convert():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify(error='Invalid or empty JSON body'), 400

        raw_pages = data.get('pages') or []
        raw_text  = (data.get('text') or '').strip()
        if not raw_pages:
            raw_pages = [raw_text] if raw_text else []

        pages = [str(p).strip() for p in raw_pages if str(p).strip()]
        if not pages:
            return jsonify(error='No text content to convert'), 400

        cfg = {
            'font_name'      : data.get('font_name','Kalam'),
            'font_size'      : max(12, min(72, int(data.get('font_size',28)))),
            'line_spacing'   : max(1.0, min(4.0, float(data.get('line_spacing',1.8)))),
            'ink_color'      : data.get('ink_color','blue'),
            'margin'         : max(20, min(200, int(data.get('margin',60)))),
            'paper_style'    : data.get('paper_style','ruled'),
            'output_format'  : data.get('output_format','pdf'),
            'page_width'     : int(data.get('page_width',794)),
            'page_height'    : int(data.get('page_height',1123)),
            'preserve_layout': bool(data.get('preserve_layout',False)),
            'layout_data'    : data.get('layout_data'),
        }

        log.info(f"Convert: {len(pages)} page(s), font={cfg['font_name']}, "
                 f"fmt={cfg['output_format']}, paper={cfg['paper_style']}")

        # Ensure fonts
        from utils.font_manager import FontManager
        FontManager(FONTS_DIR).ensure_fonts_downloaded()

        from utils.handwriting_generator import HandwritingGenerator
        gen = HandwritingGenerator(FONTS_DIR, OUTPUT_DIR)
        sid = _sid()
        fmt = cfg['output_format']

        if (cfg['preserve_layout'] and cfg['layout_data']
                and fmt in ('pdf','both')):
            from utils.handwriting_generator import PositionAwareGenerator
            PositionAwareGenerator(FONTS_DIR, OUTPUT_DIR).render_with_layout(
                cfg['layout_data'], cfg, sid)
        else:
            if fmt in ('pdf','both'):
                gen.generate_pdf(pages, cfg, sid)
            if fmt in ('jpg','both'):
                gen.generate_jpg(pages, cfg, sid)

        n = len(pages)
        out = dict(status='success', session_id=sid,
                   output_format=fmt, page_count=n)

        if fmt in ('pdf','both'):
            out['pdf_url']     = f'/api/download/{sid}/pdf'
            out['preview_url'] = f'/api/preview/{sid}'
        if fmt in ('jpg','both'):
            out['jpg_urls']    = [f'/api/download/{sid}/jpg/{i}' for i in range(n)]
            out.setdefault('preview_url', out['jpg_urls'][0] if out['jpg_urls'] else '')

        log.info(f"Convert done: session={sid}")
        return jsonify(out)

    except Exception as e:
        log.error(traceback.format_exc())
        return jsonify(error=f'Conversion failed: {e}'), 500


@app.route('/api/preview/<sid>')
def api_preview(sid):
    sid = _clean(sid)
    pdf = OUTPUT_DIR / f"{sid}.pdf"
    png = OUTPUT_DIR / f"{sid}_preview.png"
    if not pdf.exists():
        return jsonify(error='Not found'), 404
    try:
        if not png.exists():
            import fitz
            doc  = fitz.open(str(pdf))
            pix  = doc[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5))
            pix.save(str(png));  doc.close()
        return send_file(str(png), mimetype='image/png', max_age=300)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/api/download/<sid>/pdf')
def dl_pdf(sid):
    sid = _clean(sid)
    p   = OUTPUT_DIR / f"{sid}.pdf"
    if not p.exists():
        return jsonify(error='File not found – please convert again'), 404
    return send_file(str(p), as_attachment=True,
                     download_name='handwritten_notes.pdf',
                     mimetype='application/pdf')


@app.route('/api/download/<sid>/jpg/<int:pg>')
def dl_jpg(sid, pg):
    sid = _clean(sid)
    for ext in ('jpg','jpeg','png'):
        p = OUTPUT_DIR / f"{sid}_page_{pg}.{ext}"
        if p.exists():
            return send_file(str(p), as_attachment=True,
                             download_name=f'handwritten_page_{pg+1}.jpg',
                             mimetype='image/jpeg')
    return jsonify(error='Page not found'), 404


@app.route('/api/download/<sid>/all')
def dl_all(sid):
    sid   = _clean(sid)
    files = sorted(OUTPUT_DIR.glob(f"{sid}_page_*.jpg")) + \
            sorted(OUTPUT_DIR.glob(f"{sid}_page_*.png"))
    if not files:
        return jsonify(error='No pages found'), 404
    buf = io.BytesIO()
    with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as zf:
        for i,f in enumerate(files):
            zf.write(str(f), f'handwritten_page_{i+1}.jpg')
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                     download_name='handwritten_notes.zip',
                     mimetype='application/zip')


# ── Error handlers ─────────────────────────────────────────────
@app.errorhandler(413)
def too_large(_): return jsonify(error='File too large (max 50 MB)'), 413

@app.errorhandler(404)
def not_found(_):
    if request.path.startswith('/api/'): return jsonify(error='Not found'), 404
    return render_template('index.html')

@app.errorhandler(500)
def srv_err(_): return jsonify(error='Internal server error'), 500


# ── Entry ──────────────────────────────────────────────────────
if __name__ == '__main__':
    try:
        from utils.font_manager import FontManager
        FontManager(FONTS_DIR).ensure_fonts_downloaded()
    except Exception as e:
        log.warning(f"Font pre-download warning: {e}")

    port  = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
