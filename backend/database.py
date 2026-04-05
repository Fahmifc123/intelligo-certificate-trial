"""
Database module for certificate submission tracking.
Handles SQLite database operations and Google Sheets verification.
"""
import sqlite3
import os
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import logger

# Database file path
DB_FILE = "certificates.db"

# Google Sheets credentials (update with your credentials)
GOOGLE_SHEETS_CREDS_FILE = "google_sheets_creds.json"
GOOGLE_SHEET_ID = "1Xsp_bYonx9rsT7bEZOmCpaEJA7MefO_mdGNYOmIVG3o"
SHEET_NAME = "Form Responses 1"


def init_db():
    """Initialize SQLite database with certificate submissions table."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certificate_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                program_title TEXT NOT NULL,
                project_title TEXT,
                social_link TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                certificate_id TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise


def get_google_sheet_emails() -> set:
    """
    Fetch all emails from Google Sheets 'Form Responses 1' sheet.
    Returns a set of valid emails.
    """
    try:
        # Check if credentials file exists
        if not os.path.exists(GOOGLE_SHEETS_CREDS_FILE):
            logger.warning(f"Google Sheets credentials file not found: {GOOGLE_SHEETS_CREDS_FILE}")
            logger.info("Skipping Google Sheets verification")
            return None
        
        # Setup Google Sheets API
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDS_FILE, scope)
        client = gspread.authorize(creds)
        
        # Open the spreadsheet
        sheet = client.open_by_key(GOOGLE_SHEET_ID)
        worksheet = sheet.worksheet(SHEET_NAME)
        
        # Get all values from the sheet
        all_values = worksheet.get_all_values()
        
        # Extract emails from Email column (Column C = index 2)
        # Find which column has "Email" header
        emails = set()
        email_column_index = None
        
        if len(all_values) > 0:
            # Find Email column index from header row
            for idx, header in enumerate(all_values[0]):
                if header.strip().lower() == "email":
                    email_column_index = idx
                    break
        
        # Extract emails from the found column
        if email_column_index is not None and len(all_values) > 1:
            for row in all_values[1:]:  # Skip header row
                if row and len(row) > email_column_index:
                    email = row[email_column_index].strip().lower()
                    if email and "@" in email:
                        emails.add(email)
        else:
            logger.warning("Email column not found in sheet header")
        
        logger.info(f"Fetched {len(emails)} valid emails from Google Sheets")
        return emails
    except Exception as e:
        logger.error(f"Error fetching Google Sheets data: {str(e)}")
        return None


def check_email_in_form(email: str) -> bool:
    """
    Check if email exists in Google Forms response sheet.
    
    Args:
        email: Email to verify
        
    Returns:
        bool: True if email exists in form responses, False otherwise
    """
    try:
        sheet_emails = get_google_sheet_emails()
        
        # If Google Sheets fetch fails, allow submission
        if sheet_emails is None:
            logger.warning(f"Google Sheets unavailable, allowing email: {email}")
            return True
        
        is_valid = email.lower() in sheet_emails
        logger.info(f"Email validation for {email}: {is_valid}")
        return is_valid
    except Exception as e:
        logger.error(f"Error checking email in form: {str(e)}")
        # Allow submission if verification fails
        return True


def check_email_already_generated(email: str) -> bool:
    """
    Check if email has already generated a certificate.
    
    Args:
        email: Email to check
        
    Returns:
        bool: True if email already generated, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id FROM certificate_submissions WHERE email = ?",
            (email.lower(),)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        has_generated = result is not None
        logger.info(f"Certificate check for {email}: already_generated={has_generated}")
        return has_generated
    except Exception as e:
        logger.error(f"Error checking certificate generation: {str(e)}")
        return False


def save_certificate_submission(
    email: str,
    full_name: str,
    program_title: str,
    project_title: str,
    social_link: str,
    start_date: str,
    end_date: str,
    certificate_id: str
) -> bool:
    """
    Save certificate submission to database.
    
    Args:
        email: User email
        full_name: User full name
        program_title: Program title
        project_title: Project title
        social_link: Social link/media
        start_date: Certificate start date
        end_date: Certificate end date
        certificate_id: Generated certificate ID
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO certificate_submissions
            (email, full_name, program_title, project_title, social_link, start_date, end_date, certificate_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email.lower(),
                full_name,
                program_title,
                project_title,
                social_link,
                start_date,
                end_date,
                certificate_id
            )
        )
        
        conn.commit()
        conn.close()
        logger.info(f"Certificate submission saved for {email}")
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"Duplicate email submission attempt: {email}")
        return False
    except Exception as e:
        logger.error(f"Error saving certificate submission: {str(e)}")
        return False


def get_certificate_by_email(email: str) -> dict:
    """
    Get certificate information by email.
    
    Args:
        email: User email
        
    Returns:
        dict: Certificate information or None if not found
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT email, full_name, program_title, project_title, social_link,
                   start_date, end_date, certificate_id, submitted_at
            FROM certificate_submissions WHERE email = ?
            """,
            (email.lower(),)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                "email": result[0],
                "full_name": result[1],
                "program_title": result[2],
                "project_title": result[3],
                "social_link": result[4],
                "start_date": result[5],
                "end_date": result[6],
                "certificate_id": result[7],
                "submitted_at": result[8]
            }
        return None
    except Exception as e:
        logger.error(f"Error retrieving certificate: {str(e)}")
        return None


def get_all_submissions() -> list:
    """Get all certificate submissions from database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT email, full_name, program_title, project_title, social_link, certificate_id, submitted_at
            FROM certificate_submissions
            ORDER BY submitted_at DESC
            """
        )
        
        results = cursor.fetchall()
        conn.close()
        
        return [
            {
                "email": r[0],
                "full_name": r[1],
                "program_title": r[2],
                "project_title": r[3],
                "social_link": r[4],
                "certificate_id": r[5],
                "submitted_at": r[6]
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"Error retrieving submissions: {str(e)}")
        return []
