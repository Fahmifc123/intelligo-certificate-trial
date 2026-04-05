"""
Validation service module.
Contains functions for validating links, content, and uploaded files.
"""
import requests
import os
import uuid
import shutil
from fastapi import UploadFile, File

from config import (
    ALLOWED_EXTENSIONS,
    ALLOWED_CONTENT_TYPES,
    MAX_FILE_SIZE,
    UPLOADS_DIRECTORY,
    REQUIRED_KEYWORDS,
    logger
)

def validate_link(url: str) -> bool:
    """
    Validate if the social media link is accessible.
    Returns True if status_code == 200, False otherwise.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        logger.info(f"Link validation for {url}: Status {response.status_code}")
        return response.status_code == 200
    except requests.RequestException as e:
        logger.error(f"Link validation failed for {url}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error validating link {url}: {str(e)}")
        return False


def validate_content(social_link: str) -> bool:
    """
    Simulate content validation by checking if keywords exist in the URL.
    In production, this would scrape the actual content.
    """
    link_lower = social_link.lower()
    
    # Check if any keyword exists in the URL
    found_keywords = [kw for kw in REQUIRED_KEYWORDS if kw in link_lower]
    
    logger.info(f"Content validation found keywords: {found_keywords}")
    
    # For simulation, return True if at least one keyword found
    return len(found_keywords) > 0


def validate_image_file(file: UploadFile) -> tuple[bool, str]:
    """
    Validate uploaded image file.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Format file tidak didukung. Gunakan: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return False, "Tipe file tidak valid"
    
    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return False, "Ukuran file terlalu besar (maksimal 2MB)"
    
    return True, ""


def save_uploaded_file(upload_file: UploadFile) -> str:
    """
    Save uploaded file with UUID filename.
    Returns the saved file path.
    """
    # Generate unique filename
    file_ext = os.path.splitext(upload_file.filename)[1].lower()
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{file_ext}"
    
    # Create uploads directory
    os.makedirs(UPLOADS_DIRECTORY, exist_ok=True)
    
    filepath = os.path.join(UPLOADS_DIRECTORY, filename)
    
    # Save file
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    logger.info(f"File saved: {filepath}")
    return filepath


def delete_uploaded_file(filepath: str) -> bool:
    """
    Delete uploaded file from the filesystem.
    
    Args:
        filepath: Path to the file to delete
        
    Returns:
        bool: True if file was successfully deleted, False otherwise
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"File deleted: {filepath}")
            return True
        else:
            logger.warning(f"File not found for deletion: {filepath}")
            return False
    except Exception as e:
        logger.error(f"Error deleting file {filepath}: {str(e)}")
        return False
