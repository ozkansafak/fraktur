import io
from pdf2image import convert_from_bytes
from PIL import Image
import numpy as np

def process_pdf(pdf_data):
    # Convert PDF to images
    images = convert_from_bytes(pdf_data.read())
    
    processed_images = []
    for img in images:
        # Convert to numpy array
        img_array = np.array(img)
        
        # Perform preprocessing (e.g., cropping, enhancement)
        processed_img_array = preprocess_image(img_array)
        
        # Convert back to PIL Image
        processed_img = Image.fromarray(processed_img_array)
        
        # Save to bytes
        img_byte_arr = io.BytesIO()
        processed_img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        processed_images.append(img_byte_arr)
    
    return processed_images

def preprocess_image(img_array):
    # Implement your image preprocessing logic here
    # This could include cropping, contrast enhancement, noise reduction, etc.
    # For now, we'll just return the original image
    return img_array

# You can add more helper functions for specific preprocessing tasks as needed
