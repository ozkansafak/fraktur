import requests
from PIL import Image
import numpy as np 
import re
from src.processing import save_images, extract_image_bbox, compute_log_spectrum_1d
from src.utils import encode_image
from pdf2image import convert_from_path
import matplotlib.pyplot as plt

from src.utils import pylab


def construct_payload(base64_image: str, model_name: str = "gpt-4o-mini-2024-07-18") -> dict:
    """
    Constructs the payload for the GPT-4o model with a base64 encoded image.

    Args:
        base64_image (str): The base64 encoded image string.
        model_name (str): The GPT-4o model name.

    Returns:
        dict: The constructed payload for the API request.
    """
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system", "content": "You are a highly skilled OCR assistant specializing in reading German text written in the "
                "Fraktur typeface. Your task is to transcribe and translate text accurately, following a structured page layout."
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please follow these steps carefully:\n\n"
                        "1. **Transcription**: Begin by transcribing the entire page from the German Fraktur typeface into modern German text. \n\n"
                        "   - If the page contains a header or chapter heading at the top, enclose it within `<header></header>` tags.\n"
                        "   - If there is a main body of text, transcribe it and enclose it within `<german></german>` tags.\n"
                        "   - If there are footnotes or annotations at the bottom of the page, enclose them within `<footnotes></footnotes>` tags.\n\n"
                        "2. **Translation**: After the transcription of the German text is complete, translate the entire text into English.\n\n"
                        "   - Enclose the translated English text within `<english></english>` tags.\n\n"
                        "Make sure to maintain the original formatting and structure of the text, ensuring that all elements "
                        "(headers, body, and footnotes) are properly categorized and tagged. Provide both the transcribed German "
                        "text and the English translation."
              },
              {
                "type": "image_url",
                "image_url": {
                  "url": f"data:image/jpeg;base64,{base64_image}"
                }
              }
            ]
          }
        ],
        "max_tokens": 10000
    }
    return payload


def send_gpt_request(base64_image, model_name, headers: dict) -> dict:
    response = requests.post("https://api.openai.com/v1/chat/completions", 
                             json=construct_payload(base64_image, model_name), 
                             headers=headers)

    return response.json()


def single_page(fname, model_name, headers, plotter, pageno):
    # Load image
    image = convert_from_path(fname)[0]
    arr = np.array(image)
    
    # Compute log spectrum along the y-axis.
    log_spectrum_y = compute_log_spectrum_1d(arr, axis=0, plotter=plotter)
    
    # Get the bounding box pixel coordinates in x-axis.
    x_lo, x_hi = extract_image_bbox(log_spectrum_y, axis_name='y', plotter=plotter)

    # Compute log spectrum along the X-axis
    log_spectrum_x = compute_log_spectrum_1d(arr[:, x_lo:x_hi], axis=1, plotter=plotter)
    
    # G et the bounding box pixel coordinates.
    y_lo, y_hi = extract_image_bbox(log_spectrum_x, axis_name='x', plotter=plotter)
    
    # Get cropped image
    cropped_image = Image.fromarray(arr[y_lo:y_hi, x_lo:x_hi])

    # Save the original and cropped image
    save_images(y_lo, y_hi, x_lo, x_hi, arr, pageno)
    
    # convert to base64 to upload to OpenAI API
    base64_image = encode_image(cropped_image)
    
    response_dict = send_gpt_request(base64_image, model_name, headers)

    content = response_dict['choices'][0]['message']['content']
    
    # Replace repeated newline chars with single ones. '\n\n\n' -> '\n'
    content = re.sub(r'\n+', '\n', content)
    german_text = re.search(r'<german>(.*?)</german>', content, re.DOTALL).group(1)
    english_text = re.search(r'<english>(.*?)</english>', content, re.DOTALL).group(1)
    
    if plotter:
        # Plot the images with size proportional to their pixel count.
        height, width, _ = np.array(image).shape
        plt.figure(figsize=(width/500, height/500))
        plt.imshow(image); 
        plt.gca().axis('off')
        plt.show()

        plt.figure()
        height, width, _ = np.array(cropped_image).shape
        plt.figure(figsize=(width/500, height/500))
        plt.imshow(cropped_image); 
        plt.gca().axis('off')
        plt.show()

    return german_text, english_text
