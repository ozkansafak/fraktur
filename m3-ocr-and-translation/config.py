# ocr-and-translation/config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-default-secret-key')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your-openai-api-key')
    GPT_MODEL = os.getenv('GPT_MODEL', 'gpt-4o-mini-2024-07-18')
    STORAGE_SERVICE_URL = os.getenv('STORAGE_SERVICE_URL', 'http://storage-service:5004/upload')
