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

**Privacy note:** the sheet (or tab) pointed at by `GOOGLE_SHEET_ID`/`GOOGLE_SHEET_NAME` must be shared as "Anyone with the link can view" for the CSV fetch to work — anyone who knows the sheet ID can view everything in it. Since `GOOGLE_SHEET_ID` lives in this public repo/config, **don't point it at the raw form-responses sheet** (it likely has participants' names, phone numbers, etc.). Instead:

1. Create a **separate** Google Sheet containing only an Email column, e.g. cell A2 filled with `=IMPORTRANGE("<form-responses-sheet-id>", "Form Responses 1!C2:C")` (approve the IMPORTRANGE access prompt once).
2. Share that separate sheet as "Anyone with the link" → Viewer. The original form-responses sheet stays private.
3. Set `GOOGLE_SHEET_ID` to the new sheet's ID and `GOOGLE_SHEET_NAME` to its tab name (env vars, see below).

`GOOGLE_SHEET_ID` and `GOOGLE_SHEET_NAME` can be overridden via env vars if you're pointing at a different sheet per deployment.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_APP_BASE_URL` in `frontend/.env` to the backend's public URL.
