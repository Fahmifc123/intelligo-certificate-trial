from fastapi import APIRouter, UploadFile, File, Form
from services.certificate import generate_certificate
from services.validation import validate_image_file, save_uploaded_file, delete_uploaded_file
from services.ocr import extract_text_from_image, validate_ocr_text, ai_validate
from models import CertificateResponse
from config import BASE_URL, PROGRAM_TITLE, logger
from database import (
    check_email_in_form,
    check_email_already_generated,
    save_certificate_submission,
    get_certificate_by_email
)

router = APIRouter(tags=["certificates"])


@router.post("/submit")
async def submit_certificate(
    email: str = Form(...),
    full_name: str = Form(...),
    project_title: str = Form(...),
    social_link: str = Form(...),
    screenshot: UploadFile = File(...)
):
    """
    Submit a certificate for processing and verification.

    Args:
        email: User email address
        full_name: User full name
        project_title: Project title the user worked on (for record only, not in certificate)
        screenshot: Screenshot file from user

    Returns:
        Processing result with certificate ID and status

    The program/class is fixed to config.PROGRAM_TITLE since only one trial
    program is offered right now — it's not taken from client input.
    """
    try:
        # Step 1: Check if email exists in Google Forms
        is_registered, registration_error = check_email_in_form(email)
        if not is_registered:
            return {
                "success": False,
                "error": registration_error
            }
        
        # Step 2: Check if email has already generated a certificate
        if check_email_already_generated(email):
            existing_cert = get_certificate_by_email(email)
            cert_url = f"{BASE_URL}/static/certificates/generate/{existing_cert['certificate_id']}.pdf"
            return {
                "success": False,
                "error": "Email ini sudah pernah generate sertifikat sebelumnya. Hanya diperbolehkan sekali generate per email.",
                "previously_generated": {
                    "certificate_id": existing_cert["certificate_id"],
                    "certificate_url": cert_url,
                    "submitted_at": existing_cert["submitted_at"]
                }
            }
        
        # Step 3: Validate file
        is_valid, error_msg = validate_image_file(screenshot)
        if not is_valid:
            return {"success": False, "error": error_msg}
        
        # Step 4: Save uploaded file
        filepath = save_uploaded_file(screenshot)
        
        # Step 5: Extract text from image
        extracted_text = extract_text_from_image(filepath)
        
        # Step 6: Delete uploaded file after successful extraction
        delete_uploaded_file(filepath)
        
        # Step 7: Validate OCR text
        is_ocr_valid, found_keywords = validate_ocr_text(extracted_text)
        
        # Step 8: AI validation
        is_ai_valid = ai_validate(extracted_text)
        
        # Step 9: Generate certificate if all validations pass
        if is_ocr_valid and is_ai_valid:
            cert_filename = generate_certificate(full_name, PROGRAM_TITLE)
            cert_url = f"{BASE_URL}/static/certificates/generate/{cert_filename}"
            cert_id = cert_filename.replace(".pdf", "")

            # Step 10: Save submission to database
            save_certificate_submission(
                email=email,
                full_name=full_name,
                program_title=PROGRAM_TITLE,
                project_title=project_title,
                social_link=social_link,
                certificate_id=cert_id
            )

            return {
                "success": True,
                "certificate_id": cert_id,
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


@router.get("/check-certificate/{email}")
async def check_certificate(email: str):
    """
    Check if email has already generated a certificate.
    
    Args:
        email: Email address to check
        
    Returns:
        Certificate info if exists, otherwise empty
    """
    try:
        certificate = get_certificate_by_email(email)
        
        if certificate:
            return {
                "success": True,
                "exists": True,
                "certificate": certificate
            }
        else:
            return {
                "success": True,
                "exists": False
            }
    except Exception as e:
        logger.error(f"Error checking certificate: {str(e)}")
        return {"success": False, "error": str(e)}


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
        filename = generate_certificate(name, project_title)
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
