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
          {"role": "system", "content": "You have three roles. First of all you are a professional OCR assistant. "
           "Secondly, you identify the parts of your transcriptions to belong to header, body and footer sections. "
           "Lastly, you are a GERMAN to ENGLISH translator that stays loyal to the style and "
           "character of the original German text."
          },
          {
            "role": "user",
            "content": [
              {
                "type": "text",
                "text": "This work consists of three distinct subtasks:\n\n"
                        "**Step 1. OCR:** Transcribe the whole page into German and wrap the output in <raw_german></raw_german> tags. "
                        "Pay great attention to transcribing all the text and all the fraktur characters you detect in your OCR work \n\n"
                        "**Step 2. Layout Analysis:**. Look at the image of the page and your transcription again "
                        "and redo the transcription like this: \n"
                        "   - Wrap your second transcription inside <german></german> tags.\n"
                        "   - Stay loyal to the new line characters (\\n) you have transcribed in the OCR step above. "
                        "I want you to divide the parts of the transcription inside the <raw_german></raw_german> tags "
                        "into header, body, and footer sections: \n"
                        "   - If, and only if, you detected a header text (like a chapter title or a section heading), "
                        "wrap  it inside <header></header> tags. If there's no header text, "
                        "don't include any <header></header> tags at all. \n"
                        "   - Next, wrap the body of the text inside <body></body> tags. \n"
                        "   - Finally, and if, and only if, you detected any footnotes, wrap it inside <footer></footer> tags. \n\n"
                        "If there's no footer text, don't include any <footer></footer> tags at all. "
                        "**Step 3. Translation DE2EN:**. Translate the German text into English while maintaining the header, "
                        "body, and footer sections.\n\n"
                        "EXAMPLE OUTPUT FORMAT:\n"
                        "<raw_german>.................</raw_german>\n\n"
                        "<german><header>....</header>\n<body>..............</body>\n<footer>......</footer>\n</german>\n\n"
                        "<english>....................</english>\n"
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
    base64_image = encode_image(image)
    
    response_dict = send_gpt_request(base64_image, model_name, headers)

    content = response_dict['choices'][0]['message']['content']
    
    # Replace repeated newline chars with single ones. '\n\n\n' -> '\n'
    # content = re.sub(r'\n+', '\n', content)
    raw_german_text = re.search(r'<raw_german>(.*?)</raw_german>', content, re.DOTALL).group(1)
    german_text = re.search(r'<german>(.*?)</german>', content, re.DOTALL).group(1)
    english_text = re.search(r'<english>(.*?)</english>', content, re.DOTALL).group(1)
    
    if plotter:
        # Plot the images with size proportional to their pixel count.
        height, width, _ = np.array(image).shape
        plt.figure(figsize=(width/300, height/300))
        plt.imshow(image); 
        plt.gca().axis('off')
        plt.show()

        plt.figure()
        height, width, _ = np.array(cropped_image).shape
        plt.figure(figsize=(width/300, height/300))
        plt.imshow(cropped_image); 
        plt.gca().axis('off')
        plt.show()

    return raw_german_text, german_text, english_text
