# Gemini OCR + Translate (Flask)

A Flask web app that extracts text from images/PDFs using Google Gemini and translates it into multiple languages. Clean dark UI, landing page, and an upload workflow that runs on the server.

## What’s included
- Server (Flask) in ./app.py
- Pages in ./templates/
  - home.html (landing + embedded App UI at #app)
- Static assets
  - static/css/home.css (all styles)
  - static/js/home.js (all UI logic)
- Upload API: POST /upload (multipart)
- OCR: images (PNG/JPG/JPEG/GIF/BMP/WEBP) via Gemini; PDFs via pdfminer.six with Gemini OCR fallback
- Translation: strengthened prompt + post-filter to remove leftover source-language lines

## Routes
- GET / → templates/home.html (App UI is embedded under #app)
- GET /app → redirects to /#app
- POST /upload → JSON: { original_text, translated_text, target_lang, target_lang_name }

## Requirements
- Python 3.9+
- Packages: pip install -r requirements.txt
- Environment: GEMINI_API_KEY must be set (do not commit secrets)
- For scanned PDF OCR fallback, Poppler must be available (pdf2image):
  - macOS: brew install poppler
  - Ubuntu/Debian: sudo apt-get install -y poppler-utils
  - Windows: install Poppler for Windows and add bin to PATH

## Quick start
1) Install deps
   - Windows: py -m pip install -r requirements.txt
   - Linux/macOS: python3 -m pip install -r requirements.txt
2) Provide Gemini key
   - Set environment variable GEMINI_API_KEY=<your_key>
   - Or create .env with GEMINI_API_KEY=<your_key>
3) Run the server
   - Windows: py app.py
   - Linux/macOS: python3 app.py
4) Open http://localhost:7860/ → click "Open App" (scrolls to #app)

## Using the app
1) Pick an image or PDF (PNG, JPG, JPEG, GIF, BMP, WEBP, PDF)
2) Choose target language (Hindi, Spanish, French, German, Arabic, Chinese (Simplified), Japanese, Portuguese, Russian, Bengali, Tamil, Telugu, Marathi, Urdu, Korean, Italian)
3) Click Upload
4) The server will:
   - Save to temp/, resize large images for OCR
   - OCR (pdfminer for embedded PDF text; otherwise Gemini OCR for up to first 5 pages)
   - Translate with a prompt that preserves names, IDs, amounts, and dates
   - Return JSON consumed by the UI

## API details
POST /upload (multipart/form-data)
- file: image or pdf
- lang: language code (e.g., hi, es, fr, de, ...)

Response 200
```
{
  "original_text": "...",
  "translated_text": "...",
  "target_lang": "hi",
  "target_lang_name": "Hindi"
}
```

Errors
```
{ "error": "<message>" }
```

## Static hosting notes
- The App UI lives on the Home page (#app). Static preview shows the UI, but actual processing requires the Flask backend at /upload.

## Implementation notes
- app.py logs avoid printing extracted/translated text to prevent Windows console encoding issues
- Translation prompt explicitly says: translate everything, preserve layout, keep names/IDs/amounts/dates, output only translation; then a server-side filter removes leaked source-language lines

## Troubleshooting
- UI shows "API key missing on server": ensure GEMINI_API_KEY is set and restart the server
- "Cannot GET /app" at 127.0.0.1:5500: you’re on a static server. Start Flask and open http://localhost:7860/app, or from Home the link will scroll to #app on the same page
- "Upload failed":
  - Check server logs for errors
  - Ensure GEMINI_API_KEY is valid
  - For scanned PDFs, install Poppler to enable OCR fallback
- Empty or mixed-language translation: try a clearer source image/PDF; the app uses a stricter prompt and filters source-language lines

---

## Dependencies — what they are and why they’re used
The app relies on a small, focused set of Python libraries. Each has a specific role in the OCR + translation pipeline:

- Flask (== 2.0.1)
  - What: Lightweight web framework for Python.
  - Why: Serves the HTML/JS/CSS, defines routes (/ and /upload), and renders Jinja templates.
  - Notes: Paired with Werkzeug 2.0.1 to avoid version incompatibilities.

- Werkzeug (== 2.0.1)
  - What: WSGI utilities used under the hood by Flask.
  - Why: Stable, compatible HTTP request/response handling for Flask 2.0.x.

- google-generativeai (>= 0.1.0)
  - What: Official Python SDK for Google’s Gemini models.
  - Why: Used for two tasks:
    - Vision OCR: send an image alongside a prompt to extract text.
    - Translation: send extracted text with a translation prompt to produce the target language output.
  - Notes: The app targets modern model families (e.g., gemini-2.0-flash).

- Pillow (>= 9.0.0)
  - What: Imaging library for Python.
  - Why: Opens and optionally resizes large images before sending to Gemini for OCR; supports multiple image formats.

- python-dotenv (>= 0.19.0)
  - What: Loads environment variables from a .env file during local development.
  - Why: Keeps secrets (GEMINI_API_KEY) out of source code; simple config management.

- pdfminer.six (>= 20221105)
  - What: PDF text extraction library.
  - Why: First pass for PDFs — extracts embedded, selectable text quickly without OCR. Saves cost/time when PDFs already contain text.

- pdf2image (>= 1.16.3)
  - What: Converts PDF pages to images.
  - Why: Fallback for scanned PDFs with no embedded text; renders pages to PNG so Gemini Vision can OCR them.
  - System requirement: Poppler must be installed and available on PATH for rendering.

## System requirements — what and why
- Poppler
  - What: PDF rendering utilities used by pdf2image.
  - Why: Needed only for the scanned-PDF fallback path. If your PDFs have embedded text, pdfminer.six will handle them without Poppler.
  - Install:
    - macOS: `brew install poppler`
    - Ubuntu/Debian: `sudo apt-get install -y poppler-utils`
    - Windows: Install Poppler for Windows and add its `bin` folder to PATH.

## Configuration — environment variables and their purpose
- GEMINI_API_KEY
  - What: API key for Google Gemini.
  - Why: Authenticates all OCR/translation requests. Never commit this to git.
  - How: Set in your environment or a local .env file (used only for local development).

- PORT (optional, default 7860)
  - What: Port the Flask server listens on.
  - Why: Change when port 7860 is occupied or your platform requires a specific port.

## Design choices — why this stack
- Server-side OCR/translation
  - Keeps the API key private, avoids exposing it in the browser.
  - Allows pre-processing (resize images), post-processing (cleaning translations), and consistent error handling.
- Two-phase PDF handling
  - Fast embedded-text extraction first (pdfminer.six).
  - OCR fallback only when necessary (pdf2image + Gemini Vision) to reduce cost and latency.

## Security
- Do not commit keys; use environment variables or .env locally
- Uploaded files are saved to ./temp and removed after processing

## License
MIT
