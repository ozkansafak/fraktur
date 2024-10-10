# document-generation/config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-default-secret-key')
    STORAGE_SERVICE_URL = os.getenv('STORAGE_SERVICE_URL', 'http://storage-service:5004/upload')
    DOCUMENT_STORAGE_PATH = os.getenv('DOCUMENT_STORAGE_PATH', 'documents/')
