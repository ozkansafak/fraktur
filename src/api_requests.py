import aiohttp
import asyncio
from typing import Dict, Tuple, List
import time
import requests
import logging
from PIL import Image
import numpy as np 
import backoff
import re
import os
from src.processing import save_images, extract_image_bbox, compute_log_spectrum_1d
from src.utils import encode_image
from pdf2image import convert_from_path
import matplotlib.pyplot as plt
from src.utils import pylab

from src.document_generation import setup_logger

logger = logging.getLogger('logger_name')
logger.setLevel(logging.INFO)

def construct_payload_for_gpt(base64_image: str, model_name: str = "gpt-4o-mini-2024-07-18") -> dict:
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
            "role": "system", 
            "content": "You have three roles. First of all you are a professional OCR assistant. "
            "Secondly, you identify the parts of your transcriptions to belong to header, body and footer sections. "
            "Lastly, you are a GERMAN to ENGLISH translator that stays loyal to the style and "
            "character of the original German text."
          },
          {
            "role": "user",
            "content": [
              {
                "type": "text",
                "text": 
"""Instructions:

You are to perform three steps on the provided image of a document.

**Step 1: OCR Transcription**

Task: Transcribe the entire text from the image into German, including all Fraktur characters.

Attention: Pay close attention to accurately capturing all text elements. **DO NOT** summarize the table of content or index pages. Summarization of index or table of contents pages would end up in failure of the task. Capture everything on the page faithfully. 

Attention 2: Make sure you're reading each line only once. 

Formatting: Wrap the entire transcription in <raw_german></raw_german> tags.

Caution: Pay attention to identify the paragraphs as a whole and not erroneously place a carriage return at the end of each line.

Separator: When you are done with Step 1, print the separator line:

--------------------------------------------------------------------
**Step 2: Header-Body-Footer Analysis**

Review: Look at the image and your transcription from Step 1.

Verification: Ensure you haven't missed any parts; if you did, transcribe and include them now.

**Caution 1**: Pay attention to identify the paragraphs as a whole and not erroneously place a carriage return at the end of each line.
**Caution 2**: Pay close attention to accurately capturing and copying over all text elements in the content. **DO NOT** summarize any of the text content. Summarization of index or table of contents pages would end up in failure of the task. 

**Categorization**:

Header: If you detect a header (e.g., chapter title or section heading), wrap it inside <header></header> tags. If there's no header, omit the <header></header> tags.
Body: Wrap the main body of the text inside <body></body> tags.
Footer: If you detect any footnotes, wrap them inside <footer></footer> tags. If there are no footnotes, omit the <footer></footer> tags.
Formatting: Wrap this structured transcription inside <german></german> tags.

Separator: When you are done with Step 2, print the separator line again:

--------------------------------------------------------------------
**Step 3: Translation (German to English)**

Task: Translate the structured German text from Step 2 into English.
Structure: Maintain the same <header>, <body>, and <footer> sections in your translation.
Formatting: Wrap the translated text inside <english></english> tags.

Example Output Format:

<raw_german>
... (transcribed German text) ...
</raw_german>
--------------------------------------------------------------------
<german>
<header> ... </header>
<body> ... </body>
<footer> ... </footer>
</german>
--------------------------------------------------------------------
<english>
<header> ... </header>
<body> ... </body>
<footer> ... </footer>
</english>"""
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
        "max_tokens": 6000,
        "temperature": 0.1
    }
    return payload

async def make_gpt_request(base64_image: str, model_name: str, headers: dict) -> dict:
    """ Asynchronous version of send_gpt_request """

    logger.info(f"In make_gpt_request, model_name: {model_name}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.openai.com/v1/chat/completions",
            json=construct_payload_for_gpt(base64_image, model_name),
            headers=headers
        ) as response:
            return await response.json()

async def make_claude_request(base64_image: str, model_name: str="claude-3-5-sonnet-20241022") -> dict:
    """
    Make an asynchronous request to the Anthropic API w/ built-in retries and error-handling.
    """
    logger = logging.getLogger('logger_name')
    
    # @backoff.on_exception(
    #     backoff.expo,             # Use exponential backoff strategy (1s, 2s, 4s, 8s ..)
    #     (aiohttp.ClientError,     # Retry on HTTP client errors
    #     ValueError),              # Also retry on our custom ValueError
    #     max_tries=5,              # Maximum number of attempts
    #     max_time=300              # Maximum total time in seconds (5 minutes)
    #     )
    
    logger.info(f"In make_claude_request, model_name: {model_name}")
    max_retries = 5
    base_delay = 1  # Starting delay in seconds
    max_delay = 64  # Maximum delay between retries

    async def _make_request(retry_count: int = 0):
        async with aiohttp.ClientSession() as session:
            # Construct payload first to validate it
            payload = construct_payload_for_claude(base64_image, model_name)
            
            # Explicit headers with string values
            headers = {
                "x-api-key": str(os.getenv("ANTHROPIC_API_KEY")),
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            # logger.debug(f"Making request with headers: {headers}")
            
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                json=payload,
                headers=headers
            ) as response:
                if response.status == 429:
                    error_text = await response.text()
                    logger.warning(f"Rate limit hit: {error_text}.. Wait for a minute before retrying")                    
                    await asyncio.sleep(60)
                    raise ValueError("Rate limit exceeded")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"API error {response.status}: {error_text}")
                    raise ValueError(f"API returned status {response.status}")
                
                return await response.json()
    return await _make_request()

def construct_payload_for_claude(base64_image: str, model_name: str = "claude-3-5-sonnet-20241022") -> dict:
    """
    Constructs the payload for the Claude Vision model.
    """
    logger = logging.getLogger('logger_name')
    
    try:
        # Basic validation
        if not isinstance(base64_image, str):
            raise ValueError("base64_image must be a string")
        if not isinstance(model_name, str):
            raise ValueError("model_name must be a string")
            
        # Construct the payload
        payload = {
            "model": model_name,
            "system": "You have three roles. First of all you are a professional OCR assistant. "
            "Secondly, you identify the parts of your transcriptions to belong to header, body and footer sections. "
            "Lastly, you are a GERMAN to ENGLISH translator that stays loyal to the style and "
            "character of the original German text.",            
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": 
"""Instructions:

You are to perform three steps on the provided image of a document.

**Step 1: OCR Transcription**

Task: Transcribe the entire text from the image into German, including all Fraktur characters.

Attention: Pay close attention to accurately capturing all text elements. **DO NOT** summarize the table of content or index pages. Summarization of index or table of contents pages would end up in failure of the task. Capture everything on the page faithfully. 

Attention 2: Make sure you're reading each line only once. 

Formatting: Wrap the entire transcription in <raw_german></raw_german> tags.

Caution: Pay attention to identify the paragraphs as a whole and not erroneously place a carriage return at the end of each line.

Separator: When you are done with Step 1, print the separator line:

--------------------------------------------------------------------
**Step 2: Header-Body-Footer Analysis**

Review: Look at the image and your transcription from Step 1.

Verification: Ensure you haven't missed any parts; if you did, transcribe and include them now.

**Caution 1**: Pay attention to identify the paragraphs as a whole and not erroneously place a carriage return at the end of each line.
**Caution 2**: Pay close attention to accurately capturing and copying over all text elements in the content. **DO NOT** summarize any of the text content. Summarization of index or table of contents pages would end up in failure of the task. 

**Categorization**:

Header: If you detect a header (e.g., chapter title or section heading), wrap it inside <header></header> tags. If there's no header, omit the <header></header> tags.
Body: Wrap the main body of the text inside <body></body> tags.
Footer: If you detect any footnotes, wrap them inside <footer></footer> tags. If there are no footnotes, omit the <footer></footer> tags.
Formatting: Wrap this structured transcription inside <german></german> tags.

Separator: When you are done with Step 2, print the separator line again:

--------------------------------------------------------------------
**Step 3: Translation (German to English)**

Task: Translate the structured German text from Step 2 into English.
Structure: Maintain the same <header>, <body>, and <footer> sections in your translation.
Formatting: Wrap the translated text inside <english></english> tags.

Example Output Format:

<raw_german>
... (transcribed German text) ...
</raw_german>
--------------------------------------------------------------------
<german>
<header> ... </header>
<body> ... </body>
<footer> ... </footer>
</german>
--------------------------------------------------------------------
<english>
<header> ... </header>
<body> ... </body>
<footer> ... </footer>
</english>"""
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 6000,
            "temperature": 0.1
        }
        
        # Validate the constructed payload
        if not all(key in payload for key in ["model", "messages"]):
            raise ValueError("Payload missing required fields")
            
        return payload
        
    except Exception as e:
        logger.error(f"Error constructing payload: {str(e)}")
        raise

async def process_single_page(fname: str, model_name: str, headers: dict, plotter: bool, pageno: str, extract: bool = True) -> Tuple[str, str, str, str]:
    """ Asynchronously processes a single page """
    # Load and process image (this is CPU-bound, keep it synchronous)
    image = convert_from_path(fname)[0]
    arr = np.array(image)

    if extract:
        # Compute log spectrum along the y-axis.
        log_spectrum_y = compute_log_spectrum_1d(arr, axis=0, plotter=plotter)
    
        # Get the bounding box pixel coordinates in x-axis.
        x_lo, x_hi = extract_image_bbox(log_spectrum_y, axis_name='y', plotter=plotter)

        # Compute log spectrum along the X-axis
        log_spectrum_x = compute_log_spectrum_1d(arr[:, x_lo:x_hi], axis=1, plotter=plotter)

        # Get the bounding box pixel coordinates.
        y_lo, y_hi = extract_image_bbox(log_spectrum_x, axis_name='x', plotter=plotter)
    else:
        x_lo, x_hi = 0, len(arr[0])
        y_lo, y_hi = 0, len(arr)

    # Get cropped image
    cropped_image = Image.fromarray(arr[y_lo:y_hi, x_lo:x_hi])

    # Save the original and cropped image
    save_images(y_lo, y_hi, x_lo, x_hi, arr, pageno)

    # convert to base64 to upload to OpenAI API
    base64_image = encode_image(cropped_image)

    if model_name.startswith('gpt'):
        response_dict = await make_gpt_request(base64_image, model_name, headers)
    else:
        response_dict = await make_claude_request(base64_image, model_name)

    if 'content' in response_dict:
        # Anthropic model
        content = response_dict['content'][0]['text']
    elif 'choices' in response_dict:
        # OpenAI model
        content = response_dict['choices'][0]['message']['content']
    else:
        logger.error(f"Unexpected response structure: {response_dict}")
        raise ValueError("Unexpected response structure")

    content = re.sub(r'\n+', '\n', content)  # '\n\n\n' -> '\n'

    # Extract text sections (moved to separate function for clarity)
    raw_german_text = extract_text_section(pageno, content, 'raw_german')
    german_text = extract_text_section(pageno, content, 'german')
    english_text = extract_text_section(pageno, content, 'english')

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

    return content, raw_german_text, german_text, english_text

def extract_text_section(pageno: str, content: str, section: str) -> str:
    """Helper function to extract text sections with error handling"""
    
    logger = setup_logger('extract_text_section')
    
    match = re.search(f'<{section}>(.*?)</{section}>', content, re.DOTALL)
    if match is None:
        logger.info(f'Pageno: {pageno}, "{section}" section was not found')
        return ""
    return match.group(1)
