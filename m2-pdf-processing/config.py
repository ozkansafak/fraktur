# config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-default-secret-key')
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
    MINIO_HOST = os.getenv('MINIO_HOST', 'localhost:9000')
    MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
    MINIO_SECURE = os.getenv('MINIO_SECURE', 'False').lower() == 'true'
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your-openai-api-key')
    STORAGE_SERVICE_URL = os.getenv('STORAGE_SERVICE_URL', 'http://storage-service:5004/upload')
    PDF_PROCESSING_URL = os.getenv('PDF_PROCESSING_URL', 'http://pdf-processing:5001/process')
    OCR_TRANSLATION_URL = os.getenv('OCR_TRANSLATION_URL', 'http://ocr-translation:5002/ocr-translate')
    DOCUMENT_GENERATION_URL = os.getenv('DOCUMENT_GENERATION_URL', 'http://document-generation:5003/generate')
