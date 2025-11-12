# Project Setup
dev command: py app.py
Follow these steps to run the OCR + Translate project locally.

## Prerequisites
- Python 3.9+ and pip
- Poppler (for scanned-PDF OCR fallback via pdf2image)
  - macOS: `brew install poppler`
  - Ubuntu/Debian: `sudo apt-get install -y poppler-utils`
  - Windows: Install “Poppler for Windows” and add its `bin` folder to PATH

## 1) Get the code
Download or clone this repository to your machine and open the project folder.

## 2) Create and activate a virtual environment
- macOS/Linux:
  - `python3 -m venv venv`
  - `source venv/bin/activate`
- Windows (PowerShell or CMD):
  - `py -m venv venv`
  - `venv\Scripts\activate`

## 3) Install Python dependencies
- `pip install -r requirements.txt`

## 4) Configure environment variables
Create a `.env` file in the project root (same folder as `app.py`) with:
```
GEMINI_API_KEY=your_api_key_here
PORT=7860
```
Notes:
- Do not commit secrets. `.env` is read locally by the app.
- You can also set these as system environment variables instead of using `.env`.
- PORT is optional; default is 7860.

## 5) Run the server
- macOS/Linux: `python3 app.py`
- Windows: `py app.py`

You should see the server start on `http://localhost:7860/`.

## 6) Use the app
- Open `http://localhost:7860/`
- Click “App” in the navbar (or scroll to the embedded UI)
- Choose an image or PDF, select a target language, and click Upload

## Troubleshooting
- API status shows missing key → set `GEMINI_API_KEY` in `.env` or your environment and restart
- Scanned PDFs failing → ensure Poppler is installed and on PATH
- Port in use → set a different `PORT` in `.env` (e.g., 7870) and restart
- Dependency errors → re-run `pip install -r requirements.txt` inside your active virtual environment
