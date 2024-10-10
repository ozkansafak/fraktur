# frontend/app.py

import logging
from flask import Flask, render_template, request, redirect, url_for
import os
import sys
import json
import re
import time
from werkzeug.utils import secure_filename
import requests

# Configuration
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/data/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# API endpoints
PDF_PROCESSING_URL = os.getenv('PDF_PROCESSING_URL', 'http://pdf-processing:5001/process')
OCR_TRANSLATION_URL = os.getenv('OCR_TRANSLATION_URL', 'http://ocr-translation:5002/ocr-translate')
DOCUMENT_GENERATION_URL = os.getenv('DOCUMENT_GENERATION_URL', 'http://document-generation:5003/generate')

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

            # Start processing
            start_time = time.time()

            # Step 1: PDF Processing
            with open(filepath, 'rb') as f:
                files = {'file': f}
                response = requests.post(PDF_PROCESSING_URL, files=files)
            if response.status_code != 200:
                error_message = "PDF processing failed."
                logging.error(error_message)
                return render_template('upload.html', error_message=error_message)
            cropped_image_url = response.json().get('cropped_image_url')

            # Step 2: OCR and Translation
            data = {'cropped_image_url': cropped_image_url}
            response = requests.post(OCR_TRANSLATION_URL, json=data)
            if response.status_code != 200:
                error_message = "OCR and translation failed."
                logging.error(error_message)
                return render_template('upload.html', error_message=error_message)
            german_text = response.json().get('german_text')
            english_text = response.json().get('english_text')

            # Step 3: Document Generation
            data = {
                'german_text': german_text,
                'english_text': english_text
            }
            response = requests.post(DOCUMENT_GENERATION_URL, json=data)
            if response.status_code != 200:
                error_message = "Document generation failed."
                logging.error(error_message)
                return render_template('upload.html', error_message=error_message)
            document_url = response.json().get('document_url')

            processing_time = time.time() - start_time
            logging.info(f'Finished processing file: {filepath} in {processing_time:.2f} seconds')

            if not german_text and not english_text:
                error_message = "An error occurred during processing. Please try again."
                logging.error(error_message)
                return render_template('upload.html', error_message=error_message)
            
            return render_template('result.html', 
                                   german_text=german_text, 
                                   english_text=english_text, 
                                   processing_time=processing_time,
                                   document_url=document_url)
        else:
            logging.warning('Invalid file type.')
            return redirect(request.url)
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
