"""
CaseDesk AI - OCR Service
Standalone Tesseract-based OCR service for document processing
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import io
import magic
from typing import Optional
import logging

app = FastAPI(title="CaseDesk OCR Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_MIME_TYPES = {
    'image/png': 'image',
    'image/jpeg': 'image',
    'image/jpg': 'image',
    'image/tiff': 'image',
    'image/bmp': 'image',
    'application/pdf': 'pdf'
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ocr"}

@app.post("/ocr")
async def extract_text(
    file: UploadFile = File(...),
    language: str = "deu+eng"
):
    """
    Extract text from image or PDF using Tesseract OCR
    
    Args:
        file: Image or PDF file
        language: OCR language(s), default is German + English
    
    Returns:
        Extracted text and metadata
    """
    try:
        content = await file.read()
        mime_type = magic.from_buffer(content, mime=True)
        
        if mime_type not in SUPPORTED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {mime_type}. Supported: {list(SUPPORTED_MIME_TYPES.keys())}"
            )
        
        file_type = SUPPORTED_MIME_TYPES[mime_type]
        extracted_text = ""
        page_count = 1
        
        if file_type == 'pdf':
            # Convert PDF to images
            images = convert_from_bytes(content, dpi=300)
            page_count = len(images)
            texts = []
            
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image, lang=language)
                texts.append(f"--- Page {i + 1} ---\n{page_text}")
            
            extracted_text = "\n\n".join(texts)
        else:
            # Process image directly
            image = Image.open(io.BytesIO(content))
            extracted_text = pytesseract.image_to_string(image, lang=language)
        
        return {
            "success": True,
            "text": extracted_text.strip(),
            "page_count": page_count,
            "language": language,
            "mime_type": mime_type,
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"OCR processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

@app.get("/languages")
async def get_supported_languages():
    """Get list of supported OCR languages"""
    return {
        "languages": [
            {"code": "deu", "name": "German", "native": "Deutsch"},
            {"code": "eng", "name": "English", "native": "English"},
            {"code": "deu+eng", "name": "German + English", "native": "Deutsch + English"}
        ]
    }
