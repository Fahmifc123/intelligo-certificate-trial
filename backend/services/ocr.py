"""
OCR and AI validation service module.
Contains functions for extracting text from images and AI-based validation.
"""
import pytesseract
from PIL import Image
import logging
import os

from config import (
    REQUIRED_KEYWORDS,
    BONUS_KEYWORDS,
    get_openai_client,
    logger
)

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
        
        # Run OCR
        text = pytesseract.image_to_string(image, lang='eng+ind')
        
        # Convert to lowercase for easier matching
        text_lower = text.lower()
        
        logger.info(f"OCR extracted text (first 200 chars): {text_lower[:200]}...")
        
        return text_lower
        
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
            model="gpt-3.5-turbo",
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
