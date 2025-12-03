import io
from PIL import Image
import pytesseract
from typing import Optional

async def extract_text_from_image(image_content: bytes) -> str:
    """
    Extract text from image using OCR (Optical Character Recognition)
    
    Args:
        image_content: Raw image file content as bytes
        
    Returns:
        Extracted text from the image
    """
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_content))
        
        # Convert to RGB if necessary (for better OCR results)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Use pytesseract to extract text
        # Configure for Chinese and English text recognition
        custom_config = r'--oem 3 --psm 6 -l chi_sim+eng'
        
        try:
            # Try with Chinese + English
            text = pytesseract.image_to_string(image, config=custom_config)
        except:
            # Fallback to English only if Chinese model is not available
            text = pytesseract.image_to_string(image, config=r'--oem 3 --psm 6')
        
        # Clean up the extracted text
        text = text.strip()
        
        # Remove excessive whitespace and empty lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned_text = '\n'.join(lines)
        
        return cleaned_text
        
    except Exception as e:
        raise Exception(f"OCR text extraction failed: {str(e)}")

def is_tesseract_available() -> bool:
    """
    Check if Tesseract OCR is available on the system
    """
    try:
        pytesseract.get_tesseract_version()
        return True
    except:
        return False
