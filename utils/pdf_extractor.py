import logging
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Extract text and layout from PDF files"""
    
    def extract(self, file_path: str) -> Dict[str, Any]:
        """Extract text from PDF maintaining layout information"""
        doc = None
        try:
            doc = fitz.open(file_path)
            pages = []
            layout_data = []
            full_text_parts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Get page dimensions
                rect = page.rect
                page_width = rect.width
                page_height = rect.height
                
                # Extract text with detailed layout
                blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
                
                # Extract plain text for this page
                page_text = page.get_text("text")
                pages.append(page_text.strip())
                full_text_parts.append(page_text.strip())
                
                # Extract detailed layout for position-aware rendering
                page_layout = {
                    'page_num': page_num,
                    'width': page_width,
                    'height': page_height,
                    'blocks': []
                }
                
                for block in blocks.get('blocks', []):
                    if block.get('type') == 0:  # Text block
                        block_data = {
                            'type': 'text',
                            'bbox': block.get('bbox', []),
                            'lines': []
                        }
                        
                        for line in block.get('lines', []):
                            line_text = ''
                            font_size = 12
                            spans = line.get('spans', [])
                            
                            for span in spans:
                                line_text += span.get('text', '')
                                font_size = max(font_size, span.get('size', 12))
                            
                            if line_text.strip():
                                block_data['lines'].append({
                                    'text': line_text,
                                    'bbox': line.get('bbox', []),
                                    'font_size': font_size
                                })
                        
                        if block_data['lines']:
                            page_layout['blocks'].append(block_data)
                
                layout_data.append(page_layout)
            
            return {
                'full_text': '\n\n'.join(full_text_parts),
                'pages': pages,
                'page_count': len(doc),
                'layout_data': layout_data
            }
            
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise Exception(f"Failed to extract PDF: {str(e)}")
        finally:
            if doc:
                doc.close()
