# ocr-and-translation/utils.py

import requests
import base64
from PIL import Image
from io import BytesIO
import logging

def download_image(image_url: str) -> Image.Image:
    """
    Downloads an image from a given URL and returns a PIL Image object.
    
    Args:
        image_url (str): The URL of the image to download.
    
    Returns:
        PIL.Image.Image: The downloaded image.
    """
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert('RGB')
        return image
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download image from {image_url}: {e}")
        raise

def encode_image_to_base64(image: Image.Image) -> str:
    """
    Encodes a PIL Image to a base64 string.
    
    Args:
        image (PIL.Image.Image): The image to encode.
    
    Returns:
        str: The base64 encoded image string.
    """
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')
