import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import io
import re
import os

if os.name == 'nt':  # 'nt' = Windows, anything else = Linux/Mac
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp'}
MAX_FILE_SIZE_MB = 10


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_EXTENSIONS


def preprocess_image(image: Image.Image) -> Image.Image:
    """Grayscale + sharpen + contrast boost — helps with dark WhatsApp screenshots."""
    image = image.convert('L')
    image = image.filter(ImageFilter.SHARPEN)
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(2.0)


def clean_ocr_text(raw_text: str) -> str:
    """Strip blank lines, non-ASCII junk, and collapse whitespace."""
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    joined = ' '.join(lines)
    joined = re.sub(r'[^\x20-\x7E\n]', ' ', joined)
    return re.sub(r' +', ' ', joined).strip()


def extract_text_from_image(file_bytes: bytes) -> dict:
    """
    Main entry point. Takes raw image bytes, returns:
      { 'success': True,  'text': <cleaned str>, 'raw': <raw str> }
      { 'success': False, 'error': <message> }
    """
    # Size check
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return {'success': False, 'error': f'File too large ({size_mb:.1f} MB). Max is {MAX_FILE_SIZE_MB} MB.'}

    # Open image
    try:
        image = Image.open(io.BytesIO(file_bytes))
    except Exception:
        return {'success': False, 'error': 'Could not open image. Make sure it is a valid PNG, JPG, or WEBP.'}

    # Resize if very wide (Tesseract slows down on huge images)
    if image.width > 1600:
        ratio = 1600 / image.width
        image = image.resize((1600, int(image.height * ratio)), Image.LANCZOS)

    # Preprocess and OCR
    try:
        processed = preprocess_image(image)
        raw_text = pytesseract.image_to_string(processed, config='--oem 3 --psm 6')
    except pytesseract.TesseractNotFoundError:
        return {
            'success': False,
            'error': 'Tesseract binary not found. Make sure it is installed and the path is correct in ocr.py.'
        }
    except Exception as e:
        return {'success': False, 'error': f'OCR failed: {str(e)}'}

    cleaned = clean_ocr_text(raw_text)

    if len(cleaned) < 10:
        return {
            'success': False,
            'error': 'No readable text found. Try a clearer, higher-contrast screenshot.'
        }

    return {'success': True, 'text': cleaned, 'raw': raw_text}