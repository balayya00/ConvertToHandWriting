import os
import sys
import uuid
import json
import logging
import traceback
from pathlib import Path
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

UPLOAD_FOLDER = Path(tempfile.gettempdir()) / 'pdf_handwriting_uploads'
OUTPUT_FOLDER = Path(tempfile.gettempdir()) / 'pdf_handwriting_outputs'
FONTS_FOLDER = Path(__file__).parent / 'static' / 'fonts'

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)
FONTS_FOLDER.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/fonts', methods=['GET'])
def get_fonts():
    """Return available handwriting fonts"""
    from utils.font_manager import FontManager
    fm = FontManager(FONTS_FOLDER)
    fonts = fm.get_available_fonts()
    return jsonify({'fonts': fonts, 'status': 'success'})

@app.route('/api/extract', methods=['POST'])
def extract_text():
    """Extract text from uploaded file or use direct input"""
    try:
        input_type = request.form.get('input_type', 'text')
        
        if input_type == 'text':
            text = request.form.get('text', '').strip()
            if not text:
                return jsonify({'error': 'No text provided'}), 400
            return jsonify({
                'status': 'success',
                'text': text,
                'pages': [text],
                'page_count': 1
            })
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if not file or file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported file type. Please upload PDF, JPG, or PNG'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        file_path = UPLOAD_FOLDER / f"{unique_id}_{filename}"
        file.save(str(file_path))
        
        ext = filename.rsplit('.', 1)[1].lower()
        
        if ext == 'pdf':
            from utils.pdf_extractor import PDFExtractor
            extractor = PDFExtractor()
            result = extractor.extract(str(file_path))
        elif ext in ['jpg', 'jpeg', 'png']:
            from utils.ocr_extractor import OCRExtractor
            extractor = OCRExtractor()
            result = extractor.extract(str(file_path))
        else:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        # Cleanup upload
        try:
            file_path.unlink()
        except:
            pass
        
        return jsonify({
            'status': 'success',
            'text': result.get('full_text', ''),
            'pages': result.get('pages', []),
            'page_count': result.get('page_count', 1),
            'layout_data': result.get('layout_data', None)
        })
        
    except Exception as e:
        logger.error(f"Extraction error: {traceback.format_exc()}")
        return jsonify({'error': f'Extraction failed: {str(e)}'}), 500

@app.route('/api/convert', methods=['POST'])
def convert_to_handwriting():
    """Convert text to handwritten output"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        text = data.get('text', '').strip()
        pages = data.get('pages', [text] if text else [])
        
        if not pages or not any(p.strip() for p in pages):
            return jsonify({'error': 'No text to convert'}), 400
        
        settings = {
            'font_name': data.get('font_name', 'HomemadeApple'),
            'font_size': int(data.get('font_size', 28)),
            'line_spacing': float(data.get('line_spacing', 1.8)),
            'ink_color': data.get('ink_color', 'blue'),
            'margin': int(data.get('margin', 60)),
            'paper_style': data.get('paper_style', 'ruled'),
            'output_format': data.get('output_format', 'pdf'),
            'page_width': int(data.get('page_width', 794)),
            'page_height': int(data.get('page_height', 1123)),
        }
        
        from utils.handwriting_generator import HandwritingGenerator
        from utils.font_manager import FontManager
        
        fm = FontManager(FONTS_FOLDER)
        fm.ensure_fonts_downloaded()
        
        generator = HandwritingGenerator(FONTS_FOLDER, OUTPUT_FOLDER)
        
        output_format = settings['output_format']
        unique_id = str(uuid.uuid4())
        
        if output_format in ['pdf', 'both']:
            pdf_path = generator.generate_pdf(pages, settings, unique_id)
        
        if output_format in ['jpg', 'both']:
            jpg_paths = generator.generate_jpg(pages, settings, unique_id)
        
        result = {
            'status': 'success',
            'session_id': unique_id,
            'output_format': output_format,
            'page_count': len(pages)
        }
        
        if output_format in ['pdf', 'both']:
            result['pdf_url'] = f'/api/download/{unique_id}/pdf'
        if output_format in ['jpg', 'both']:
            result['jpg_urls'] = [f'/api/download/{unique_id}/jpg/{i}' for i in range(len(pages))]
            result['preview_url'] = f'/api/download/{unique_id}/jpg/0'
        elif output_format == 'pdf':
            result['preview_url'] = f'/api/preview/{unique_id}'
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Conversion error: {traceback.format_exc()}")
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

@app.route('/api/preview/<session_id>', methods=['GET'])
def preview_page(session_id):
    """Generate preview image from PDF first page"""
    try:
        pdf_path = OUTPUT_FOLDER / f"{session_id}.pdf"
        if not pdf_path.exists():
            return jsonify({'error': 'Session not found'}), 404
        
        import fitz
        doc = fitz.open(str(pdf_path))
        page = doc[0]
        mat = fitz.Matrix(1.5, 1.5)
        pix = page.get_pixmap(matrix=mat)
        img_path = OUTPUT_FOLDER / f"{session_id}_preview.png"
        pix.save(str(img_path))
        doc.close()
        
        return send_file(str(img_path), mimetype='image/png')
    except Exception as e:
        logger.error(f"Preview error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<session_id>/pdf', methods=['GET'])
def download_pdf(session_id):
    """Download generated PDF"""
    pdf_path = OUTPUT_FOLDER / f"{session_id}.pdf"
    if not pdf_path.exists():
        return jsonify({'error': 'File not found. Please convert again.'}), 404
    
    return send_file(
        str(pdf_path),
        as_attachment=True,
        download_name='handwritten_notes.pdf',
        mimetype='application/pdf'
    )

@app.route('/api/download/<session_id>/jpg/<int:page_num>', methods=['GET'])
def download_jpg(session_id, page_num):
    """Download generated JPG for specific page"""
    jpg_path = OUTPUT_FOLDER / f"{session_id}_page_{page_num}.jpg"
    if not jpg_path.exists():
        # Try PNG
        jpg_path = OUTPUT_FOLDER / f"{session_id}_page_{page_num}.png"
    if not jpg_path.exists():
        return jsonify({'error': 'File not found. Please convert again.'}), 404
    
    return send_file(
        str(jpg_path),
        as_attachment=True,
        download_name=f'handwritten_page_{page_num + 1}.jpg',
        mimetype='image/jpeg'
    )

@app.route('/api/download/<session_id>/all', methods=['GET'])
def download_all_jpg(session_id):
    """Download all JPG pages as ZIP"""
    import zipfile
    import io
    
    jpg_files = list(OUTPUT_FOLDER.glob(f"{session_id}_page_*.jpg"))
    png_files = list(OUTPUT_FOLDER.glob(f"{session_id}_page_*.png"))
    all_files = jpg_files + png_files
    
    if not all_files:
        return jsonify({'error': 'No files found'}), 404
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for i, f in enumerate(sorted(all_files)):
            zf.write(str(f), f'handwritten_page_{i+1}.jpg')
    
    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        as_attachment=True,
        download_name='handwritten_notes.zip',
        mimetype='application/zip'
    )

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 50MB'}), 413

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html')

if __name__ == '__main__':
    # Initialize fonts on startup
    try:
        from utils.font_manager import FontManager
        fm = FontManager(FONTS_FOLDER)
        fm.ensure_fonts_downloaded()
        logger.info("Fonts initialized successfully")
    except Exception as e:
        logger.warning(f"Font initialization warning: {e}")
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'production') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
