"""
Configuration module for Intelligo Certificate System.
Contains app settings, constants, and global configurations.
"""
import os
import logging

# Setup logging - suppress noisy third-party loggers
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress noisy third-party loggers
for noisy_logger in ['comtypes', 'PIL', 'urllib3', 'charset_normalizer']:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

# App Configuration
APP_TITLE = "Intelligo ID Certificate System"
APP_DESCRIPTION = "Trial Bootcamp Certificate Generation API"
APP_VERSION = "1.0.0"

# CORS Settings
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://*.vercel.app",
]

# Static Files
STATIC_DIRECTORY = "static"
UPLOADS_DIRECTORY = os.path.join(STATIC_DIRECTORY, "uploads")
CERTIFICATES_DIRECTORY = os.path.join(STATIC_DIRECTORY, "certificates")

# File Upload Settings
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/jpg'}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

# Validation Keywords
REQUIRED_KEYWORDS = ["intelligo", "#intelligoid", "bootcamp", "trial"]
BONUS_KEYWORDS = ["project", "data", "analysis", "ai", "machine learning", "python"]

# Certificate Settings
CERTIFICATE_TEMPLATE = "INT-TBDSAI-{month}{year}-{file_id}"
BASE_URL = "http://43.134.70.75:8002"

# In-memory storage for duplicate prevention
processed_emails = set()

# OpenAI Client (lazy initialization)
openai_client = None


def get_openai_client():
    """Initialize OpenAI client lazily."""
    global openai_client
    if openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            from openai import OpenAI
            openai_client = OpenAI(api_key=api_key)
    return openai_client
