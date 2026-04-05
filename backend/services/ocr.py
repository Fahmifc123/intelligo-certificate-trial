"""
OCR and AI validation service module.
Contains functions for extracting text from images and AI-based validation.
"""
import os
import shutil
import platform
from PIL import Image
import logging

# Dynamically detect Tesseract path based on OS
def get_tesseract_path() -> str:
    """Get Tesseract executable path for current OS."""
    # Check environment variable first
    env_path = os.environ.get('TESSERACT_CMD')
    if env_path and os.path.exists(env_path):
        return env_path
    
    # Check if tesseract is in PATH
    system_tesseract = shutil.which('tesseract')
    if system_tesseract and os.path.exists(system_tesseract):
        return system_tesseract
    
    # Windows default
    if platform.system() == 'Windows':
        win_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        if os.path.exists(win_path):
            return win_path
    
    # Linux common paths
    linux_paths = ['/usr/bin/tesseract', '/usr/local/bin/tesseract']
    for path in linux_paths:
        if os.path.exists(path):
            return path
    
    # Fallback to PATH lookup
    if system_tesseract:
        return system_tesseract
    
    raise FileNotFoundError("Tesseract OCR not found. Please install Tesseract.")

tesseract_path = get_tesseract_path()
os.environ['TESSERACT_CMD'] = tesseract_path

import pytesseract

from config import (
    REQUIRED_KEYWORDS,
    BONUS_KEYWORDS,
    get_openai_client,
    logger
)

# Configure pytesseract (use inner module for older versions)
pytesseract.pytesseract.tesseract_cmd = tesseract_path

def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from image using OCR (Tesseract).
    Returns lowercase text for easier matching.
    """
    try:
        logger.info(f"Running OCR on image: {image_path}")
        
        # Open image
        image = Image.open(image_path)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Extract text using pytesseract
        text = pytesseract.image_to_string(image, lang='eng+ind')
        
        if text.strip():
            text_lower = text.lower()
            return text_lower
        
        logger.warning("No text extracted from image")
        return ""
        
    except Exception as e:
        logger.error(f"OCR extraction failed: {str(e)}")
        return ""


def validate_ocr_text(text: str) -> tuple[bool, list[str]]:
    """
    Validate OCR extracted text for required keywords.
    
    Returns:
        tuple: (is_valid, found_keywords)
    """
    found_required = [kw for kw in REQUIRED_KEYWORDS if kw in text]
    found_bonus = [kw for kw in BONUS_KEYWORDS if kw in text]
    
    logger.info(f"OCR validation - Required found: {found_required}")
    logger.info(f"OCR validation - Bonus found: {found_bonus}")
    
    # Valid if at least one required keyword found
    is_valid = len(found_required) > 0
    
    return is_valid, found_required + found_bonus


def ai_validate(text: str) -> bool:
    """
    Use OpenAI API to validate if the text is proof of social media sharing.
    
    Returns True if VALID, False otherwise.
    """
    client = get_openai_client()
    
    # If no API key configured, skip AI validation
    if client is None:
        logger.warning("OpenAI API key not configured, skipping AI validation")
        return True
    
    try:
        logger.info("Running AI validation...")
        
        prompt = f"""Determine if this text is proof that a user shared a bootcamp project on social media.

Text:
{text[:1000]}

Answer only:
VALID or INVALID"""
        
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "system", "content": "You are a validation assistant. Answer only VALID or INVALID."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=10,
            temperature=0
        )
        
        answer = response.choices[0].message.content.strip().upper()
        logger.info(f"AI validation result: {answer}")
        
        return answer == "VALID"
        
    except Exception as e:
        logger.error(f"AI validation failed: {str(e)}")
        # If AI fails, default to True (don't block user)
        return True
