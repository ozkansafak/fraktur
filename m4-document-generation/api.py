# document-generation/api.py

from flask import Flask, request, jsonify
import logging
from generate_document import generate_document
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(level=logging.INFO)

@app.route('/generate', methods=['POST'])
def generate():
    """
    Endpoint to generate a .docx document from German and English texts.
    
    Expected JSON Payload:
    {
        "german_text": "Original German transcription...",
        "english_text": "Translated English text..."
    }
    
    Returns JSON Response:
    {
        "document_url": "http://storage-service:5004/documents/document_id.docx"
    }
    """
    try:
        data = request.get_json()
        if not data or 'german_text' not in data or 'english_text' not in data:
            logging.warning("Invalid request payload.")
            return jsonify({"error": "Invalid request payload. 'german_text' and 'english_text' are required."}), 400
        
        german_text = data['german_text']
        english_text = data['english_text']
        logging.info("Received document generation request.")
        
        document_url = generate_document(german_text, english_text, Config)
        
        if not document_url:
            logging.error("Document URL not returned after generation.")
            return jsonify({"error": "Document generation failed."}), 500
        
        return jsonify({"document_url": document_url}), 200
    
    except Exception as e:
        logging.exception("Exception occurred during document generation.")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)
