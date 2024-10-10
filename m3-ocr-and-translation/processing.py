# ocr-and-translation/processing.py

import openai
import logging
from utils import download_image, encode_image_to_base64
import re

def perform_ocr_and_translation(image_url: str, config) -> dict:
    """
    Performs OCR on the image and translates the extracted German text to English.
    
    Args:
        image_url (str): URL of the cropped PDF image.
        config (Config): Configuration object containing API keys and settings.
    
    Returns:
        dict: Dictionary containing 'german_text' and 'english_text'.
    """
    try:
        # Download and encode the image
        image = download_image(image_url)
        base64_image = encode_image_to_base64(image)
        
        # Set OpenAI API key
        openai.api_key = config.OPENAI_API_KEY
        
        # Construct the payload
        payload = {
            "model": config.GPT_MODEL,
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
                            "text": 
"""Instructions:

You are to perform three steps on the provided image of a document.

**Step 1: OCR Transcription**

Task: Transcribe the entire text from the image into German, including all Fraktur characters.

Attention: Pay close attention to accurately capturing all text elements.

Attention 2: Make sure you're reading each line only once. 

Formatting: Wrap the entire transcription in <raw_german></raw_german> tags.

Caution: Pay attention to identify the paragraphs as a whole and not erroneously place a carriage return at the end of each line.

Separator: When you are done with Step 1, print the separator line:

--------------------------------------------------------------------
**Step 2: Header-Body-Footer Analysis**

Review: Look at the image and your transcription from Step 1.

Verification: Ensure you haven't missed any parts; if you did, transcribe and include them now.

Caution: Pay attention to identify the paragraphs as a whole and not erroneously place a carriage return at the end of each line.

Categorization:

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
            "max_tokens": 3000,
            "temperature": 0.1
        }
        
        # Make the API request
        response = openai.ChatCompletion.create(**payload)
        
        content = response.choices[0].message['content']
        
        # Replace repeated newline chars with a single one. '\n\n\n' -> '\n'
        content = re.sub(r'\n+', '\n', content)
        
        # Extract raw German OCR'ed text.
        match = re.search(r'<raw_german>(.*?)</raw_german>', content, re.DOTALL)
        if match:
            raw_german_text = match.group(1).strip()
        else:
            logging.warning(r'"<raw_german>(.*?)</raw_german>" was not found')
            raw_german_text = ''
        
        # Extract structured German text
        match = re.search(r'<german>(.*?)</german>', content, re.DOTALL)
        if match:
            german_text = match.group(1).strip()
        else:
            logging.warning(r'"<german>(.*?)</german>" was not found in the response.')
            german_text = ''
        
        # Extract english translation
        match = re.search(r'<english>(.*?)</english>', content, re.DOTALL)
        if match:
            english_text = match.group(1).strip()
        else:
            logging.warning(r'"<english>(.*?)</english>" was not found in the response.')
            english_text = ''
        
        return {
            'raw_german_text': raw_german_text,
            'german_text': german_text,
            'english_text': english_text
        }
        
    except Exception as e:
        logging.exception("Error during OCR and translation process.")
        raise
