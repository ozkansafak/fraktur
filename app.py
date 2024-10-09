import logging
from flask import Flask, render_template, request, redirect, url_for
import os
import sys
import json
import re
import time
from werkzeug.utils import secure_filename

# Add the 'src' directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils import encode_image
from src.api_requests import single_page

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Set your OpenAI API key
import openai
openai.api_key = os.getenv("OPENAI_API_KEY")

# Headers for OpenAI API requests
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {openai.api_key}"
}

# Model name
model_name = "gpt-4o-mini-2024-07-18"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'pdf_file' not in request.files:
            logging.warning('No file part in the request.')
            return redirect(request.url)
        file = request.files['pdf_file']
        # If the user does not select a file
        if file.filename == '':
            logging.warning('No selected file.')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Process the uploaded PDF page
            pageno = 'uploaded_page'  # You can generate a unique identifier if needed
            logging.info(f'Start processing file: {filepath}')
            start_time = time.time()
            content, raw_german_text, german_text, english_text = single_page(
                filepath, model_name, headers, plotter=False, pageno=pageno, output_dir=app.config['UPLOAD_FOLDER']
            )
            processing_time = time.time() - start_time
            logging.info(f'Finished processing file: {filepath} in {processing_time:.2f} seconds')

            if not german_text and not english_text:
                error_message = "An error occurred during processing. Please try again."
                logging.error(error_message)
                return render_template('upload.html', error_message=error_message)
            
            return render_template('result.html', german_text=german_text, english_text=english_text, processing_time=processing_time)
        else:
            logging.warning('Invalid file type.')
            return redirect(request.url)
    return render_template('upload.html')


if __name__ == '__main__':
    app.run(debug=True)
