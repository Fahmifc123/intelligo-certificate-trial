from fastapi import APIRouter, UploadFile, File, Form
from services.certificate import generate_certificate
from services.validation import validate_image_file, save_uploaded_file
from services.ocr import extract_text_from_image, validate_ocr_text, ai_validate
from models import CertificateResponse
from config import BASE_URL, logger

router = APIRouter(tags=["certificates"])


@router.post("/submit")
async def submit_certificate(
    email: str = Form(...),
    full_name: str = Form(...),
    program_title: str = Form(...),
    project_title: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    screenshot: UploadFile = File(...)
):
    """
    Submit a certificate for processing and verification.
    
    Args:
        email: User email address
        full_name: User full name
        program_title: Program name (e.g., "Trial Bootcamp Data Science & AI - Intelligo ID")
        project_title: Project title the user worked on (for record only, not in certificate)
        start_date: Start date (e.g., "23 October 2025")
        end_date: End date (e.g., "27 October 2025")
        screenshot: Screenshot file from user
        
    Returns:
        Processing result with certificate ID and status
    """
    try:
        # Validate file
        is_valid, error_msg = validate_image_file(screenshot)
        if not is_valid:
            return {"success": False, "error": error_msg}
        
        # Save uploaded file
        filepath = save_uploaded_file(screenshot)
        
        # Extract text from image
        extracted_text = extract_text_from_image(filepath)
        
        # Validate OCR text
        is_ocr_valid, found_keywords = validate_ocr_text(extracted_text)
        
        # AI validation
        is_ai_valid = ai_validate(extracted_text)
        
        # Generate certificate if all validations pass
        if is_ocr_valid and is_ai_valid:
            cert_filename = generate_certificate(full_name, program_title, start_date, end_date)
            cert_url = f"{BASE_URL}/static/certificates/generate/{cert_filename}"

            return {
                "success": True,
                "certificate_id": cert_filename.replace(".pdf", ""),
                "certificate_url": cert_url,
                "email": email,
                "name": full_name,
                "keywords_found": found_keywords
            }
        else:
            return {
                "success": False,
                "error": "Validation failed. Please ensure certificate contains required information.",
                "details": {
                    "ocr_valid": is_ocr_valid,
                    "ai_valid": is_ai_valid,
                    "keywords_found": found_keywords
                }
            }
            
    except Exception as e:
        logger.error(f"Error processing certificate: {str(e)}")
        return {"success": False, "error": f"Processing error: {str(e)}"}


@router.post("/generate-dummy", response_model=CertificateResponse)
async def generate_dummy_certificate(
    name: str = Form(...),
    email: str = Form(...),
    project_title: str = Form(...),
    social_link: str = Form(...)
):
    """
    Generate a certificate with dummy data (bypasses all validation).
    Use this for testing the certificate template only.
    """
    logger.info(f"Generating dummy certificate for {email}")
    
    try:
        # Use dummy dates for testing
        start_date = "23 October 2025"
        end_date = "27 October 2025"
        
        filename = generate_certificate(name, project_title, start_date, end_date)
        certificate_url = f"{BASE_URL}/static/certificates/generate/{filename}"
        
        logger.info(f"Dummy certificate generated: {certificate_url}")
        
        return CertificateResponse(
            status="success",
            certificate_url=certificate_url,
            message="Certificate successfully generated",
            ai_validation=True
        )
        
    except Exception as e:
        logger.error(f"Dummy certificate generation failed: {str(e)}")
        return CertificateResponse(
            status="error",
            message=f"Failed to generate certificate: {str(e)}"
        )
