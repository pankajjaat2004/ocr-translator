# Project Deep Dive — File‑wise Documentation

This document explains the structure and flow of the codebase, optimized for local development.

## Table of Contents
- Overview
- Runtime Flow
- Backend (Flask)
  - app.py
    - Environment loading and API configuration
    - Health test: test_gemini_api()
    - OCR: extract_text_with_gemini()
    - PDF handling: extract_text_from_pdf()
    - Translation pipeline: translate_text() and _strip_source_from_translation()
    - Routes: `/`, `/app`, `/upload`
    - Startup
- Frontend
  - templates/home.html (Landing + Embedded App)
  - static/css/home.css (Styles)
  - static/js/home.js (Client logic)
- Requirements and Third‑Party Libraries
- Error Handling & Logging
- Security & Privacy
- Static Hosting Notes
- Troubleshooting

---

## Overview
Gemini OCR + Translate is a Flask app that extracts text from images/PDFs with Google Gemini and translates it to a selected language. The UI is embedded directly on the landing page for a simple, local‑first experience.

Key goals:
- Robust server‑side OCR/translation
- Clean, responsive UI
- Minimal setup for local runs

## Runtime Flow
1) User opens `/` (Home). The navbar “App” link anchors to `#app` on the same page.
2) The embedded UI lets the user pick a file and language.
3) Submitting the form POSTs multipart data to `/upload`.
4) The server stores the file temporarily under `./temp`, then:
   - If image: OCR with Gemini Vision
   - If PDF: try embedded text first (pdfminer), otherwise render pages and OCR
5) The text is translated with a strict prompt and lightly filtered to remove echoed source lines.
6) JSON response updates the two result panels.
7) Temp file is removed.

---

## Backend (Flask)
### File: app.py
Core application: routes, OCR/translation functions, and startup.

#### Environment loading and API configuration
- `dotenv.load_dotenv()` loads `.env` for local development.
- `GEMINI_API_KEY` is read from the environment. Do not hardcode secrets.
- `google.generativeai.configure(api_key=...)` is set when making requests.

#### Health test: test_gemini_api()
Creates a `GenerativeModel('gemini-2.0-flash')` and performs a simple request to validate connectivity.

#### OCR: extract_text_with_gemini(image_path)
- Retries up to 3 times.
- Resizes very large images (max dimension 1024) to improve reliability.
- Sends `[prompt, image]` to Gemini Vision and returns `response.text.strip()`.

#### PDF handling: extract_text_from_pdf(pdf_path)
- First tries `pdfminer.high_level.extract_text` for embedded text.
- If empty, falls back to `pdf2image.convert_from_path` (Poppler required) to rasterize up to the first 5 pages and OCRs each image.

#### Translation pipeline: translate_text(text, lang_code)
- Maps the language code to a human‑readable name.
- Uses `gemini-2.0-flash` with a strict prompt (translate everything; preserve layout; keep names/IDs/amounts/dates; output only translation).
- Filters echoed source lines with `_strip_source_from_translation`.

#### Routes
- `GET /` → `render_template('home.html', gemini_api_key=api_key)`
- `GET /app` → `redirect('/#app')` (shortcut to the embedded UI)
- `POST /upload` → JSON `{ original_text, translated_text, target_lang, target_lang_name }`

#### Startup
- Ensures `templates/` exists.
- Runs API connectivity test and prints status.
- Listens on `0.0.0.0` with `PORT` (default 7860).

---

## Frontend
### File: templates/home.html (Landing + Embedded App)
- Navbar, hero, Features, How it works, and About sections.
- The App UI is embedded under `#app` in the hero card.
- Uses Jinja to inject a key presence indicator and links local assets with:
  - `<link rel="stylesheet" href="{{ url_for('static', filename='css/home.css') }}">`
  - `<script src="{{ url_for('static', filename='js/home.js') }}"></script>`

### File: static/css/home.css (Styles)
- Theme variables and dark layout
- Navbar, hero, sections, footer styles
- Embedded App UI (panel, uploader, grid, cards)
- Responsive behaviors for laptop and smaller screens

### File: static/js/home.js (Client logic)
- Sets footer year and API status indicator
- Handles file upload form: builds `FormData`, POSTs to `/upload`, renders results/errors
- Updates language label based on selection

All CSS/JS are local files (no CDNs). Templates reference them via Flask’s `url_for('static', ...)` for reliable local use.

---

## Requirements and Third‑Party Libraries
- Flask, Jinja2
- google‑generativeai (Gemini SDK)
- Pillow
- pdfminer.six
- pdf2image (requires Poppler installed)
- python‑dotenv

---

## Error Handling & Logging
- Consistent try/except and retries for OCR/translation
- Logs include lengths rather than full texts to avoid console encoding issues
- `/upload` returns structured JSON errors

---

## Security & Privacy
- Do not commit secrets; read `GEMINI_API_KEY` from environment or `.env` locally
- Uploaded files go to `./temp` and are removed after processing

---

## Static Hosting Notes
- This project is designed to run locally with Flask. Opening templates directly as static files will not execute server logic and Jinja tags may not resolve.
- For full functionality, start the Flask server and use `http://localhost:7860/` (the “App” link jumps to `/#app`).

---

## Troubleshooting
- API status shows missing key → ensure `GEMINI_API_KEY` is set, then restart the server
- "Cannot GET /app" on a static server → start Flask and open `http://localhost:7860/app` (redirects to `/#app`) or use the Home page link to scroll to the embedded UI
- "Upload failed" → check server logs, validate the API key, and ensure Poppler is installed for scanned PDFs
- Mixed or partial translation → try clearer scans; the prompt plus filter reduces source‑line leakage
