# pdf-processing/processing.py

import numpy as np
from PIL import Image
from pdf2image import convert_from_path
import logging
from utils import compute_log_spectrum_1d, extract_image_bbox

def process_pdf(filepath: str) -> Image.Image:
    """
    Processes a PDF file to crop the image containing text.
    
    Args:
        filepath (str): Path to the PDF file.
    
    Returns:
        PIL.Image.Image: Cropped image.
    """
    # Convert PDF to Image
    images = convert_from_path(filepath)
    image = images[0]  # Assuming single-page PDF

    arr = np.array(image)

    # Compute log spectrum along the y-axis.
    log_spectrum_y = compute_log_spectrum_1d(arr, axis=0, plotter=False)

    # Get the bounding box pixel coordinates in x-axis.
    x_lo, x_hi = extract_image_bbox(log_spectrum_y, axis_name='y', plotter=False)

    # Compute log spectrum along the X-axis
    log_spectrum_x = compute_log_spectrum_1d(arr[:, x_lo:x_hi], axis=1, plotter=False)

    # Get the bounding box pixel coordinates in y-axis.
    y_lo, y_hi = extract_image_bbox(log_spectrum_x, axis_name='x', plotter=False)

    # Get cropped image
    cropped_image = Image.fromarray(arr[y_lo:y_hi, x_lo:x_hi])

    return cropped_image
