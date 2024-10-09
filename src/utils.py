import logging

import time 
from PIL import Image
from io import BytesIO
import base64
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab

pylab.rcParams.update(
    {
        "legend.fontsize": "small",
        "font.size": 12,
        "figure.figsize": (6*1, 2.2*1),
        "axes.labelsize": "small",
        "axes.titlesize": "medium",
        "axes.grid": "on",
        "xtick.labelsize": "small",
        "ytick.labelsize": "small",
    }
)

def timeit(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        delta = end - start
        logging.info(f"{func.__name__} runtime: {delta:.2f} sec")
    
        return result
    return wrapper


def encode_image(image: Image.Image) -> str:
    """
    Encodes the PIL input image to a base64 string. (To be used to send to OpenAI API endpoint)

    Args:
        image (PIL.Image.Image): The image to encode.

    Returns:
        str: The base64 encoded image string.
    """
    buffered = BytesIO()
    image.save(buffered, format="JPEG")

    return base64.b64encode(buffered.getvalue()).decode('utf-8')

