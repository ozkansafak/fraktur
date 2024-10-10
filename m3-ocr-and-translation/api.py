# ocr-and-translation/api.py

from flask import Flask, request, jsonify
import logging
from processing import perform_ocr_and_translation
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route('/ocr-translate', methods=['POST'])
def ocr_translate():
    """
    Endpoint to perform OCR and translation on a cropped PDF image.
    
    Expected JSON Payload:
    {
        "cropped_image_url": "http://storage-service:5004/path/to/cropped_image.jpg"
    }
    
    Returns JSON Response:
    {
        "raw_german_text": "...",
        "german_text": "...",
        "english_text": "..."
    }
    """
    try:
        data = request.get_json()
        if not data or 'cropped_image_url' not in data:
            logging.warning("Invalid request payload.")
            return jsonify({"error": "Invalid request payload. 'cropped_image_url' is required."}), 400
        
        cropped_image_url = data['cropped_image_url']
        logging.info(f"Received OCR and translation request for image URL: {cropped_image_url}")
        
        result = perform_ocr_and_translation(cropped_image_url, Config)
        
        if not result['german_text'] and not result['english_text']:
            logging.error("OCR and translation failed to produce any text.")
            return jsonify({"error": "OCR and translation failed."}), 500
        
        return jsonify(result), 200
    
    except Exception as e:
        logging.exception("Exception occurred during OCR and translation.")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
