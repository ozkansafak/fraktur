# pdf-processing/api.py

from flask import Flask, request, jsonify
import os
import logging
from processing import process_pdf
import uuid
import requests
from config import Config

app = Flask(__name__)
UPLOAD_FOLDER = '/data/uploads'
CROPPED_FOLDER = '/data/cropped'
STORAGE_SERVICE_URL = Config.STORAGE_SERVICE_URL

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CROPPED_FOLDER, exist_ok=True)

@app.route('/process', methods=['POST'])
def process():
    if 'file' not in request.files:
        logging.warning('No file part in the request.')
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        logging.warning('No selected file.')
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        try:
            cropped_image = process_pdf(filepath)
            cropped_filename = f"cropped_{filename}.jpg"
            cropped_path = os.path.join(CROPPED_FOLDER, cropped_filename)
            cropped_image.save(cropped_path, format='JPEG')

            # Upload cropped image to Storage Service
            with open(cropped_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(STORAGE_SERVICE_URL, files=files)
            if response.status_code != 200:
                logging.error('Failed to upload cropped image to storage service.')
                return jsonify({'error': 'Failed to upload cropped image'}), 500
            cropped_image_url = response.json().get('file_url')

            return jsonify({'cropped_image_url': cropped_image_url}), 200
        except Exception as e:
            logging.exception('Error processing PDF.')
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
