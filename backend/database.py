"""
Database module for certificate submission tracking.
Handles SQLite database operations and Google Sheets verification.
"""
import csv
import io
import sqlite3
import os
from datetime import datetime
from urllib.parse import quote
import requests
from config import logger

# Database file path
DB_FILE = "certificates.db"

# Registration verification reads a public CSV export of a Google Sheet —
# no service account/credentials file needed. The sheet (or, for privacy, a
# separate sheet that only exposes an Email column via IMPORTRANGE) must be
# shared as "Anyone with the link" (Viewer). See README for setup.
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1Xsp_bYonx9rsT7bEZOmCpaEJA7MefO_mdGNYOmIVG3o")
SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Form Responses 1")


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
    Fetch all emails from a public CSV export of the registration Google
    Sheet. Requires no credentials, but the sheet must be shared as
    "Anyone with the link" (Viewer) — otherwise Google returns an HTML
    login/error page instead of CSV and this returns None (verification
    unavailable).

    Returns:
        set of valid emails, or None if the sheet couldn't be read.
    """
    url = (
        f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/gviz/tq"
        f"?tqx=out:csv&sheet={quote(SHEET_NAME)}"
    )
    try:
        response = requests.get(url, timeout=10)

        if response.status_code != 200 or "text/csv" not in response.headers.get("Content-Type", ""):
            logger.error(
                f"Failed to fetch registration sheet as CSV (HTTP {response.status_code}). "
                "Make sure the sheet is shared as 'Anyone with the link can view' "
                f"and that GOOGLE_SHEET_NAME ('{SHEET_NAME}') matches an existing tab."
            )
            return None

        rows = list(csv.reader(io.StringIO(response.text)))
        if not rows:
            logger.warning("Registration sheet CSV is empty")
            return None

        # Find which column has the "Email" header
        email_column_index = next(
            (idx for idx, header in enumerate(rows[0]) if header.strip().lower() == "email"),
            None
        )
        if email_column_index is None:
            logger.warning("Email column not found in registration sheet header")
            return None

        emails = set()
        for row in rows[1:]:
            if len(row) > email_column_index:
                email = row[email_column_index].strip().lower()
                if email and "@" in email:
                    emails.add(email)

        logger.info(f"Fetched {len(emails)} valid emails from registration sheet")
        return emails
    except requests.RequestException as e:
        logger.error(f"Error fetching registration sheet: {str(e)}")
        return None


def check_email_in_form(email: str) -> tuple[bool, str]:
    """
    Check if email exists in Google Forms response sheet.

    Fails closed: if the sheet can't be reached (missing/invalid
    credentials, network error, etc.), the email is rejected rather than
    silently let through, since that would let unregistered people claim
    certificates whenever Google Sheets verification is misconfigured.

    Args:
        email: Email to verify

    Returns:
        tuple: (is_allowed, error_message). error_message is "" when allowed.
    """
    try:
        sheet_emails = get_google_sheet_emails()

        if sheet_emails is None:
            logger.error(
                f"Google Sheets verification unavailable, rejecting email: {email}"
            )
            return False, (
                "Sistem verifikasi pendaftaran sedang bermasalah. "
                "Silakan coba lagi beberapa saat lagi atau hubungi panitia."
            )

        is_valid = email.lower() in sheet_emails
        logger.info(f"Email validation for {email}: {is_valid}")
        if not is_valid:
            return False, (
                "Email tidak ditemukan dalam daftar peserta form. "
                "Pastikan Anda telah mengisi form terlebih dahulu."
            )
        return True, ""
    except Exception as e:
        logger.error(f"Error checking email in form: {str(e)}")
        return False, (
            "Sistem verifikasi pendaftaran sedang bermasalah. "
            "Silakan coba lagi beberapa saat lagi atau hubungi panitia."
        )


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
        certificate_id: Generated certificate ID

    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # start_date/end_date are no longer collected per-submission, but the
        # columns stay (NOT NULL) for compatibility with existing databases,
        # so they're just written as empty strings.
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
                "",
                "",
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


def delete_submission_by_email(email: str) -> bool:
    """
    Delete a certificate submission by email, allowing that email to
    generate a certificate again (used by the admin dashboard's reset).

    Args:
        email: User email

    Returns:
        bool: True if a row was deleted, False if no matching row existed.
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM certificate_submissions WHERE email = ?",
            (email.lower(),)
        )
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()
        logger.info(f"Admin reset submission for {email}: deleted={deleted}")
        return deleted
    except Exception as e:
        logger.error(f"Error deleting submission for {email}: {str(e)}")
        return False


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
