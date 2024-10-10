# document-generation/processing.py

import os
import logging
from utils import create_document, upload_document
import uuid

def generate_document(german_text: str, english_text: str, config) -> str:
    """
    Generates a .docx document from German and English texts and uploads it to Storage Service.
    
    Args:
        german_text (str): Extracted German transcription.
        english_text (str): Translated English text.
        config (Config): Configuration object containing storage settings.
    
    Returns:
        str: URL of the uploaded .docx document.
    """
    try:
        # Generate a unique filename
        document_id = str(uuid.uuid4())
        filename = f"document_{document_id}.docx"
        output_path = os.path.join('/app/output', filename)
        
        # Ensure the output directory exists
        os.makedirs('/app/output', exist_ok=True)
        
        # Create the document
        create_document(german_text, english_text, config, output_path)
        logging.info(f"Generated document at {output_path}")
        
        # Upload the document to Storage Service
        document_url = upload_document(output_path, config)
        logging.info(f"Uploaded document to {document_url}")
        
        return document_url
    except Exception as e:
        logging.exception("Error during document generation.")
        raise
