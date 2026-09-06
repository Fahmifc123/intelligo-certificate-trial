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

Google Sheets registration verification (`database.py`) checks the submitted email against the "Email" column of a public CSV export of a Google Sheet — no service account or credentials file needed, just an HTTP GET to `https://docs.google.com/spreadsheets/d/<id>/gviz/tq?tqx=out:csv&sheet=<name>`. It **fails closed**: if the sheet can't be fetched as CSV (not shared publicly, wrong ID/tab name, network error), submissions are rejected (not silently allowed) so unregistered people can't claim certificates just because verification is misconfigured.

To enable it, share the sheet at `GOOGLE_SHEET_ID` (defaults to the "Form Responses 1" sheet) as **"Anyone with the link" → Viewer**: open the sheet → Share (top right) → General access → change from "Restricted" to "Anyone with the link". No code or env var changes needed if you're keeping the default sheet.

Note: since `GOOGLE_SHEET_ID` lives in this repo/config, sharing that sheet publicly means anyone who has the ID can view its full contents (not just emails). If that's ever a concern, point `GOOGLE_SHEET_ID`/`GOOGLE_SHEET_NAME` (env vars) at a separate sheet instead that only exposes an Email column via `IMPORTRANGE`, and keep the original responses sheet private.

### Admin dashboard

A minimal dashboard at `/admin` on the frontend lists every certificate submission and lets you reset one (delete its row, so that email can submit/generate again) without touching the database by hand.

It's disabled by default. To enable it, set `ADMIN_API_KEY` in the backend's `.env` to a long random value and restart the backend — the dashboard's login screen asks for this same value, sent as the `X-Admin-Key` header on every admin request. Without `ADMIN_API_KEY` set, `/admin/*` endpoints return 503 rather than being open with no password.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_APP_BASE_URL` in `frontend/.env` to the backend's public URL.
