# intelligo-certificate-trial

Certificate claim system for Intelligo ID trial bootcamp participants. Participants submit their name, class, and proof of a social media post; the backend verifies it (Google Sheets registration check, OCR + AI validation) and generates a PDF certificate from a PPTX template.

## Backend

### System dependencies

The backend shells out to system binaries for OCR and PDF generation. Without these installed, submissions will silently fail or the app can crash on startup:

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-ind libreoffice-impress
```

- `tesseract-ocr` + `tesseract-ocr-ind` — reads the required keywords (English + Indonesian) off the uploaded screenshot. If missing, OCR validation is skipped rather than blocking users, but proof screenshots won't be checked.
- `libreoffice-impress` (not just `libreoffice-core`) — required to convert the generated PPTX certificate to PDF. Without it, every certificate generation fails with "Cannot convert PPTX to PDF".

### Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # if present, then fill in OPENAI_API_KEY, BASE_URL, etc.
./start.sh
```

Environment variables (see `config.py`):
- `BASE_URL` — public base URL used to build certificate download links (e.g. `https://api.yourdomain.com`). Defaults to `http://127.0.0.1:8002`.
- `OPENAI_API_KEY` — optional; if unset, AI validation is skipped and OCR keyword matching alone is used.

Google Sheets registration verification (`database.py`) checks the submitted email against the "Email" column of the `Form Responses 1` sheet at `GOOGLE_SHEET_ID`. It **fails closed**: if `google_sheets_creds.json` is missing, invalid, or the sheet can't be reached, submissions are rejected (not silently allowed) so unregistered people can't claim certificates just because verification is misconfigured. To enable it:

1. Create a Google Cloud service account and enable the Google Sheets API + Google Drive API for it.
2. Download the service account's JSON key.
3. Share the Google Sheet with the service account's email (Viewer access is enough).
4. Place the JSON key at `backend/google_sheets_creds.json` (or point `GOOGLE_SHEETS_CREDS_FILE` at another path).

`GOOGLE_SHEETS_CREDS_FILE`, `GOOGLE_SHEET_ID`, and `GOOGLE_SHEET_NAME` can all be overridden via env vars if you're pointing at a different sheet per deployment.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_APP_BASE_URL` in `frontend/.env` to the backend's public URL.
