from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
import requests
import time
import uuid
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from typing import Optional
import logging

# NEW: OCR and AI imports
import pytesseract
from PIL import Image
from openai import OpenAI
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Intelligo ID Certificate System",
    description="Trial Bootcamp Certificate Generation API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files setup
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage for duplicate prevention
processed_emails = set()

# NEW: OpenAI client initialization (will use API key from environment)
openai_client = None

def get_openai_client():
    """Initialize OpenAI client lazily."""
    global openai_client
    if openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            openai_client = OpenAI(api_key=api_key)
    return openai_client

# Data Model
class CertificateRequest(BaseModel):
    name: str
    email: EmailStr
    project_title: str
    social_link: str

class CertificateResponse(BaseModel):
    status: str
    certificate_url: Optional[str] = None
    message: Optional[str] = None
    ocr_text: Optional[str] = None  # NEW: For debugging
    ai_validation: Optional[bool] = None  # NEW: AI validation result

# Validation Functions
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
    keywords = ["intelligo", "trial", "bootcamp"]
    link_lower = social_link.lower()
    
    # Check if any keyword exists in the URL
    found_keywords = [kw for kw in keywords if kw in link_lower]
    
    logger.info(f"Content validation found keywords: {found_keywords}")
    
    # For simulation, return True if at least one keyword found
    # In real implementation, this would fetch and parse the actual content
    return len(found_keywords) > 0


# ============================================
# NEW: OCR AND AI VALIDATION FUNCTIONS
# ============================================

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
    # Required keywords (must contain at least one)
    required_keywords = ["intelligo", "#intelligoid", "bootcamp", "trial"]
    
    # Bonus keywords (nice to have)
    bonus_keywords = ["project", "data", "analysis", "ai", "machine learning", "python"]
    
    found_required = [kw for kw in required_keywords if kw in text]
    found_bonus = [kw for kw in bonus_keywords if kw in text]
    
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
    
    # If no API key configured, skip AI validation (return True)
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
    upload_dir = os.path.join("static", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    filepath = os.path.join(upload_dir, filename)
    
    # Save file
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    logger.info(f"File saved: {filepath}")
    return filepath


def validate_image_file(file: UploadFile) -> tuple[bool, str]:
    """
    Validate uploaded image file.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    # Check file extension
    allowed_extensions = {'.jpg', '.jpeg', '.png'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        return False, f"Format file tidak didukung. Gunakan: {', '.join(allowed_extensions)}"
    
    # Check content type
    allowed_types = {'image/jpeg', 'image/png', 'image/jpg'}
    if file.content_type not in allowed_types:
        return False, "Tipe file tidak valid"
    
    # Check file size (max 2MB)
    max_size = 2 * 1024 * 1024  # 2MB in bytes
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > max_size:
        return False, "Ukuran file terlalu besar (maksimal 2MB)"
    
    return True, ""

def generate_certificate(name: str, project_title: str) -> str:
    """
    Generate a PDF certificate with professional template and return the file path.
    Template includes:
    - Elegant border design
    - Intelligo branding with logo
    - Participant name with decorative elements
    - Program details with current date
    - Issue ID in bottom right
    - Professional signature area
    """
    # Generate unique filename and issue ID
    file_id = str(uuid.uuid4())[:8].upper()
    issue_id = f"INT-TBDSAI-{datetime.now().strftime('%m%y')}-{file_id}"
    filename = f"{file_id}.pdf"
    filepath = os.path.join("static", "certificates", filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Create PDF
    c = canvas.Canvas(filepath, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # Colors
    primary_orange = colors.HexColor("#FF5400")
    dark_navy = colors.HexColor("#023047")
    white = colors.HexColor("#FFFFFF")
    black = colors.HexColor("#1a1a1a")
    gray = colors.HexColor("#6b7280")
    light_gray = colors.HexColor("#f3f4f6")
    gold = colors.HexColor("#fbbf24")
    
    # === BACKGROUND ===
    c.setFillColor(white)
    c.rect(0, 0, width, height, fill=True, stroke=False)
    
    # === ELEGANT BORDER ===
    border_margin = 30
    c.setStrokeColor(primary_orange)
    c.setLineWidth(3)
    c.rect(border_margin, border_margin, width - 2*border_margin, height - 2*border_margin, fill=False, stroke=True)
    
    # Inner border
    inner_margin = 40
    c.setStrokeColor(light_gray)
    c.setLineWidth(1)
    c.rect(inner_margin, inner_margin, width - 2*inner_margin, height - 2*inner_margin, fill=False, stroke=True)
    
    # === HEADER SECTION ===
    # Orange accent bar at top
    c.setFillColor(primary_orange)
    c.rect(border_margin, height - 100, width - 2*border_margin, 8, fill=True, stroke=False)
    
    # === INTELLIGO LOGO & BRANDING ===
    logo_x = 80
    logo_y = height - 70
    
    # Logo circle background
    c.setFillColor(primary_orange)
    c.circle(logo_x, logo_y, 25, fill=True, stroke=False)
    
    # Logo text "I"
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(logo_x, logo_y - 7, "I")
    
    # Brand name
    c.setFillColor(dark_navy)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(logo_x + 40, logo_y + 5, "INTELLIGO.ID")
    
    c.setFillColor(gray)
    c.setFont("Helvetica", 10)
    c.drawString(logo_x + 40, logo_y - 12, "Data Science & AI Bootcamp")
    
    # === CERTIFICATE TITLE ===
    c.setFillColor(dark_navy)
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(width - 80, height - 60, "CERTIFICATE")
    
    c.setFillColor(gray)
    c.setFont("Helvetica", 10)
    c.drawRightString(width - 80, height - 75, "OF PARTICIPATION")
    
    # === DECORATIVE LINE ===
    line_y = height - 130
    c.setStrokeColor(gold)
    c.setLineWidth(2)
    center_x = width / 2
    c.line(center_x - 80, line_y, center_x + 80, line_y)
    
    # === MAIN CONTENT ===
    content_y = height - 180
    
    # "This is to certify that" text
    c.setFillColor(gray)
    c.setFont("Helvetica", 14)
    c.drawCentredString(width/2, content_y, "This is to certify that")
    
    # === PARTICIPANT NAME ===
    name_y = content_y - 50
    c.setFillColor(dark_navy)
    c.setFont("Times-Bold", 36)
    c.drawCentredString(width/2, name_y, name)
    
    # Decorative underline for name
    c.setStrokeColor(primary_orange)
    c.setLineWidth(2)
    name_width = c.stringWidth(name, "Times-Bold", 36)
    c.line(width/2 - name_width/2 - 20, name_y - 10, width/2 + name_width/2 + 20, name_y - 10)
    
    # === PARTICIPATION DETAILS ===
    details_y = name_y - 60
    c.setFillColor(gray)
    c.setFont("Helvetica", 13)
    c.drawCentredString(width/2, details_y, "has successfully participated in")
    
    # === PROGRAM NAME ===
    program_y = details_y - 35
    c.setFillColor(dark_navy)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width/2, program_y, "Trial Bootcamp Data Science & AI")
    
    # === PROJECT TITLE ===
    project_y = program_y - 30
    c.setFillColor(primary_orange)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, project_y, f'"{project_title}"')
    
    # === DATE ===
    date_y = project_y - 40
    current_date = datetime.now().strftime("%B %Y")
    c.setFillColor(gray)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, date_y, f"held in {current_date}")
    
    # === SIGNATURE SECTION ===
    sig_y = 100
    
    # Left side - Signature
    c.setStrokeColor(black)
    c.setLineWidth(1)
    c.line(80, sig_y, 220, sig_y)
    
    c.setFillColor(dark_navy)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(80, sig_y - 18, "Muhammad Fahmi")
    
    c.setFillColor(gray)
    c.setFont("Helvetica", 10)
    c.drawString(80, sig_y - 32, "Head of Learning")
    c.drawString(80, sig_y - 44, "Intelligo ID")
    
    # Right side - Issue ID
    c.setFillColor(dark_navy)
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(width - 80, sig_y - 18, "Certificate ID:")
    
    c.setFillColor(primary_orange)
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - 80, sig_y - 35, issue_id)
    
    # === FOOTER ===
    footer_y = 50
    c.setFillColor(light_gray)
    c.rect(0, 0, width, footer_y, fill=True, stroke=False)
    
    c.setFillColor(gray)
    c.setFont("Helvetica", 8)
    c.drawCentredString(width/2, 25, "This certificate is issued by Intelligo ID | www.intelligo.id")
    
    # Orange accent in footer
    c.setFillColor(primary_orange)
    c.rect(0, 0, width * 0.3, 4, fill=True, stroke=False)
    
    # Save PDF
    c.save()
    
    logger.info(f"Certificate generated: {filepath} with Issue ID: {issue_id}")
    return filename

# API Endpoints

# ============================================
# MODIFIED: Updated endpoint with file upload
# ============================================
@app.post("/submit", response_model=CertificateResponse)
async def submit_certificate_request(
    name: str = Form(...),
    email: str = Form(...),
    project_title: str = Form(...),
    social_link: str = Form(...),
    screenshot: UploadFile = File(...)
):
    """
    Submit a certificate request with screenshot upload.
    
    Validation flow:
    1. Validate image file
    2. Save uploaded image
    3. Validate social media link
    4. Extract text via OCR
    5. Validate OCR keywords
    6. Run AI validation
    7. Generate certificate if all pass
    """
    logger.info(f"Received submission from {email}")
    
    # Check for duplicate submission
    if email in processed_emails:
        logger.warning(f"Duplicate submission attempt from {email}")
        return CertificateResponse(
            status="error",
            message="Sertifikat sudah pernah dibuat untuk email ini."
        )
    
    # ============================================
    # STEP 1: Validate image file
    # ============================================
    logger.info("Validating uploaded image...")
    is_file_valid, error_msg = validate_image_file(screenshot)
    
    if not is_file_valid:
        logger.warning(f"File validation failed: {error_msg}")
        return CertificateResponse(
            status="error",
            message=error_msg
        )
    
    # ============================================
    # STEP 2: Save uploaded image
    # ============================================
    try:
        image_path = save_uploaded_file(screenshot)
        logger.info(f"Screenshot saved: {image_path}")
    except Exception as e:
        logger.error(f"Failed to save file: {str(e)}")
        return CertificateResponse(
            status="error",
            message="Gagal menyimpan file. Silakan coba lagi."
        )
    
    # ============================================
    # STEP 3: Validate social media link
    # ============================================
    logger.info("Validating social media link...")
    is_link_valid = validate_link(social_link)
    
    if not is_link_valid:
        logger.warning(f"Link validation failed for {social_link}")
        # Clean up saved file
        if os.path.exists(image_path):
            os.remove(image_path)
        return CertificateResponse(
            status="error",
            message="Link tidak valid. Pastikan link postingan dapat diakses."
        )
    
    # ============================================
    # STEP 4: Extract text via OCR
    # ============================================
    logger.info("Running OCR on screenshot...")
    ocr_text = extract_text_from_image(image_path)
    
    if not ocr_text:
        logger.warning("OCR extraction returned empty text")
        # Clean up saved file
        if os.path.exists(image_path):
            os.remove(image_path)
        return CertificateResponse(
            status="error",
            message="Screenshot tidak mengandung teks yang dapat dibaca. Pastikan gambar jelas."
        )
    
    # ============================================
    # STEP 5: Validate OCR keywords
    # ============================================
    logger.info("Validating OCR text...")
    is_ocr_valid, found_keywords = validate_ocr_text(ocr_text)
    
    if not is_ocr_valid:
        logger.warning(f"OCR validation failed. Found keywords: {found_keywords}")
        # Clean up saved file
        if os.path.exists(image_path):
            os.remove(image_path)
        return CertificateResponse(
            status="error",
            message="Screenshot tidak mengandung bukti posting. Pastikan terlihat tag @intelligo.id atau hashtag yang sesuai.",
            ocr_text=ocr_text[:500] if os.getenv("DEBUG") else None
        )
    
    logger.info(f"OCR validation passed. Found keywords: {found_keywords}")
    
    # ============================================
    # STEP 6: Run AI validation
    # ============================================
    logger.info("Running AI validation...")
    is_ai_valid = ai_validate(ocr_text)
    
    if not is_ai_valid:
        logger.warning("AI validation failed")
        # Clean up saved file
        if os.path.exists(image_path):
            os.remove(image_path)
        return CertificateResponse(
            status="error",
            message="Konten tidak valid (AI validation failed). Pastikan screenshot menunjukkan postingan bootcamp project.",
            ocr_text=ocr_text[:500] if os.getenv("DEBUG") else None,
            ai_validation=False
        )
    
    logger.info("AI validation passed")
    
    # ============================================
    # STEP 7: Simulate processing delay
    # ============================================
    logger.info("Processing... waiting 3 seconds")
    time.sleep(3)
    
    # ============================================
    # STEP 8: Generate certificate
    # ============================================
    try:
        filename = generate_certificate(name, project_title)
        certificate_url = f"http://localhost:8000/static/certificates/{filename}"
        
        # Mark email as processed
        processed_emails.add(email)
        
        logger.info(f"Certificate generated successfully: {certificate_url}")
        
        return CertificateResponse(
            status="success",
            certificate_url=certificate_url,
            message="Sertifikat berhasil dibuat",
            ai_validation=True
        )
        
    except Exception as e:
        logger.error(f"Certificate generation failed: {str(e)}")
        # Clean up saved file
        if os.path.exists(image_path):
            os.remove(image_path)
        return CertificateResponse(
            status="error",
            message="Gagal membuat sertifikat. Silakan coba lagi."
        )

@app.post("/generate-dummy", response_model=CertificateResponse)
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
        certificate_url = f"http://localhost:8000/static/certificates/{filename}"
        
        logger.info(f"Dummy certificate generated: {certificate_url}")
        
        return CertificateResponse(
            status="success",
            certificate_url=certificate_url,
            message="Sertifikat dummy berhasil dibuat",
            ai_validation=True
        )
        
    except Exception as e:
        logger.error(f"Dummy certificate generation failed: {str(e)}")
        return CertificateResponse(
            status="error",
            message=f"Gagal membuat sertifikat: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Intelligo ID Certificate API"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Intelligo ID Certificate System API",
        "version": "1.0.0",
        "endpoints": {
            "submit": "POST /submit",
            "health": "GET /health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
