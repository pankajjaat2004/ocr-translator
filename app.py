import os
from flask import Flask, render_template, request, jsonify, redirect
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv
import time
import traceback
import sys
import json
from pdfminer.high_level import extract_text as pdf_extract_text

# Load environment variables
load_dotenv()

# Configure Gemini API with key from environment variable
api_key = os.getenv("GEMINI_API_KEY")


# Function to test API connectivity
def test_gemini_api():
    try:
        genai.configure(api_key=api_key)
        
        # Test with a simple text prompt using the latest model
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Hello, please respond with 'API is working'")
        
        if not response or not hasattr(response, 'text') or not response.text:
            print("WARNING: Received empty response during API test")
            return False
            
        print(f"API Test Response: {response.text.strip()}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to connect to Gemini API: {str(e)}")
        print(traceback.format_exc())
        return False

# Initialize Flask app
app = Flask(__name__)

# Supported languages for translation
language_map = {
    'hi': 'Hindi', 'es': 'Spanish', 'fr': 'French', 'de': 'German', 'ar': 'Arabic',
    'zh': 'Chinese (Simplified)', 'ja': 'Japanese', 'pt': 'Portuguese', 'ru': 'Russian',
    'bn': 'Bengali', 'ta': 'Tamil', 'te': 'Telugu', 'mr': 'Marathi', 'ur': 'Urdu',
    'ko': 'Korean', 'it': 'Italian'
}

# Configure error responses
@app.errorhandler(500)
def server_error(e):
    return jsonify(error="Internal server error: " + str(e)), 500

def extract_text_with_gemini(image_path):
    """Extract text from image using Gemini Vision model"""
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} to extract text using Gemini...")
            
            # Updated model options to use the latest available models
            model_options = ['gemini-2.0-flash']
            
            for model_name in model_options:
                try:
                    print(f"Trying model: {model_name}")
                    model = genai.GenerativeModel(model_name)
                    break
                except Exception as model_error:
                    print(f"Error with model {model_name}: {str(model_error)}")
                    if model_name == model_options[-1]:  # Last model option
                        raise
                    continue

            # Load the image
            with Image.open(image_path) as img:
                print(f"Image loaded from {image_path} (Size: {img.size}, Format: {img.format})")
                
                # Resize image if too large (API may have size limits)
                max_dimension = 1024
                if img.width > max_dimension or img.height > max_dimension:
                    print(f"Resizing large image from {img.width}x{img.height}")
                    ratio = min(max_dimension / img.width, max_dimension / img.height)
                    new_width = int(img.width * ratio)
                    new_height = int(img.height * ratio)
                    img = img.resize((new_width, new_height))
                    print(f"Resized to {new_width}x{new_height}")
                    img.save(image_path)  # Save resized image
                
                # Create prompt for text extraction
                prompt = "Extract all the text from this image. Return only the extracted text, nothing else."

                # Generate response with image
                print("Sending request to Gemini API for text extraction...")
                response = model.generate_content([prompt, img])

                # Validate response
                if not response or not hasattr(response, 'text') or not response.text:
                    raise ValueError("Received empty response from Gemini API")

                extracted_text = response.text.strip()
                print(f"Successfully extracted text (length: {len(extracted_text)})")
                return extracted_text
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            print(traceback.format_exc())
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            return f"Could not extract text from the image: {str(e)}"


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF: try embedded text first; fallback to OCR of first pages if available."""
    try:
        text = pdf_extract_text(pdf_path) or ""
        if text.strip():
            return text.strip()
    except Exception as e:
        print(f"PDF text extraction error: {str(e)}")
        print(traceback.format_exc())

    try:
        from pdf2image import convert_from_path
        pages = convert_from_path(pdf_path, dpi=200, fmt='png')
        results = []
        for i, page in enumerate(pages[:5]):
            temp_img_path = os.path.join('temp', f"pdf_page_{int(time.time())}_{i}.png")
            page.save(temp_img_path, 'PNG')
            try:
                results.append(extract_text_with_gemini(temp_img_path))
            finally:
                try:
                    if os.path.exists(temp_img_path):
                        os.remove(temp_img_path)
                except Exception:
                    pass
        combined = "\n\n".join([r for r in results if r])
        return combined.strip() if combined.strip() else "No text found in PDF."
    except Exception as e:
        print(f"PDF OCR fallback unavailable: {str(e)}")
        print(traceback.format_exc())
        return "No embedded text found in PDF, and OCR fallback is unavailable on this server."


def _strip_source_from_translation(source: str, translated: str) -> str:
    try:
        if not source or not translated:
            return translated or ""
        src_lines = [ln.strip() for ln in source.splitlines() if ln.strip()]
        out = translated
        for ln in src_lines:
            # Remove only lines that are clearly source-language (contain ASCII letters) to avoid removing numeric-only lines
            if len(ln) >= 6 and any(('A' <= ch <= 'Z') or ('a' <= ch <= 'z') for ch in ln) and all(ord(ch) < 128 for ch in ln):
                out = out.replace(ln, "")
        # Collapse extra blank lines
        cleaned = "\n".join([l for l in (ln.rstrip() for ln in out.splitlines()) if l.strip() != "" or l == ""])
        return cleaned.strip()
    except Exception:
        return translated


def translate_text(text, lang_code='hi'):
    """Translate text to the target language using Gemini and remove any leaked source lines from output"""
    max_retries = 3
    retry_delay = 2

    if not text or text.strip() == "":
        return "No text to translate."
    if text.startswith("Could not extract text from the image"):
        return "Cannot translate due to OCR failure."

    code = (lang_code or 'hi').lower()
    target_name = language_map.get(code, 'Hindi')

    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} to translate text using Gemini to {target_name}...")
            model_options = ['gemini-2.0-flash']
            for model_name in model_options:
                try:
                    print(f"Trying model: {model_name}")
                    model = genai.GenerativeModel(model_name)
                    break
                except Exception as model_error:
                    print(f"Error with model {model_name}: {str(model_error)}")
                    if model_name == model_options[-1]:
                        raise
                    continue

            prompt = (
                f"You are a professional translator. Translate ALL of the following text to {target_name}. "
                f"Preserve line breaks and layout. Keep proper names, organizations, roll numbers, amounts, and dates unchanged. "
                f"Do NOT include any of the original source-language lines in the output. Output ONLY the translation text with no extras.\n\n"
                f"--- BEGIN SOURCE ---\n{text}\n--- END SOURCE ---"
            )

            print("Sending request to Gemini API for translation...")
            response = model.generate_content(prompt)
            if not response or not hasattr(response, 'text') or not response.text:
                raise ValueError("Received empty response from Gemini API")

            translated_text = (response.text or "").strip()
            translated_text = _strip_source_from_translation(text, translated_text)
            print(f"Successfully translated text (length: {len(translated_text)})")
            return translated_text
        except Exception as e:
            print(f"Translation attempt {attempt + 1} failed: {str(e)}")
            print(traceback.format_exc())
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                continue
            return f"Translation failed: {str(e)}"


@app.route('/')
def home():
    return render_template('home.html', gemini_api_key=api_key)


@app.route('/app')
def app_page():
    return redirect('/#app')


@app.route('/upload', methods=['POST'])
def upload_file():
    print("Received upload request")
    if 'file' not in request.files:
        print("No file part in the request")
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        print("No file selected")
        return jsonify({'error': 'No file selected'}), 400

    # Check file extension
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        print(f"Invalid file format: {file.filename}")
        return jsonify({'error': 'Invalid file format. Please upload an image or PDF (PNG, JPG, JPEG, GIF, BMP, WEBP, PDF).'}), 400

    temp_path = None
    try:
        # Create temp directory if it doesn't exist
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        print(f"Ensuring temp directory exists: {temp_dir}")

        # Make sure the temp directory has write permissions
        try:
            if not os.access(temp_dir, os.W_OK):
                os.chmod(temp_dir, 0o755)  # chmod to ensure write permissions
                print(f"Updated permissions for temp directory: {temp_dir}")
        except Exception as perm_error:
            print(f"Warning: Could not update permissions: {str(perm_error)}")

        # Save the uploaded file temporarily with a unique name and original extension
        ext = file.filename.rsplit('.', 1)[1].lower()
        temp_filename = f"upload_{int(time.time())}.{ext}"
        temp_path = os.path.join(temp_dir, temp_filename)
        print(f"Saving uploaded file to {temp_path}")

        file.save(temp_path)
        
        # Ensure the file has appropriate permissions
        try:
            os.chmod(temp_path, 0o644)  # Make the file readable
            print(f"Updated permissions for file: {temp_path}")
        except Exception as file_perm_error:
            print(f"Warning: Could not update file permissions: {str(file_perm_error)}")

        # Extract text (PDF or Image)
        print("Starting text extraction...")
        if ext == 'pdf':
            extracted_text = extract_text_from_pdf(temp_path)
        else:
            extracted_text = extract_text_with_gemini(temp_path)
        print(f"Text extraction completed. Length: {len(extracted_text)} characters")

        # Translate text
        print("Starting text translation...")
        lang_code = (request.form.get('lang') or 'hi').lower()
        if lang_code not in language_map:
            lang_code = 'hi'
        translated_text = translate_text(extracted_text, lang_code)
        print(f"Translation completed. Length: {len(translated_text)} characters")

        return jsonify({
            'original_text': extracted_text,
            'translated_text': translated_text,
            'target_lang': lang_code,
            'target_lang_name': language_map.get(lang_code)
        })
    except Exception as e:
        error_msg = f"Error processing image: {str(e)}"
        print(error_msg)
        print(traceback.format_exc())
        return jsonify({
            'error': error_msg
        }), 500
    finally:
        # Clean up temporary file if it exists
        try:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
                print(f"Removed temporary file: {temp_path}")
        except Exception as e:
            print(f"Failed to remove temporary file: {str(e)}")
            # Don't let this failure affect the response


if __name__ == '__main__':
    # Ensure the template folder exists
    if not os.path.exists('templates'):
        os.makedirs('templates')
        print("Created 'templates' directory. Please place your HTML files here.")

    # Test API connectivity at startup
    api_working = test_gemini_api()
    if api_working:
        print("Gemini API connection successful!")
    else:
        print("WARNING: Gemini API connection failed. The application may not work correctly!")

    # For Hugging Face Spaces, we need to listen on 0.0.0.0 and port 7860
    print(f"Starting Flask app on port {os.environ.get('PORT', 7860)}")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 7860)))
