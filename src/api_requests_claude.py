import aiohttp
import asyncio
from typing import Dict, Tuple, List
import logging
from PIL import Image
import numpy as np 
import ipdb
import re
import os
import openai
from src.processing import save_images, extract_image_bbox, compute_log_spectrum_1d
from src.utils import pylab, plt, encode_image, log_execution_time, count_num_tokens
from src.constants import FRAGMENTED_SENTENCES_SYSTEM_PROMPT, FRAGMENTED_SENTENCES_USER_PROMPT
from src.constants import THREE_ROLE_USER_PROMPT, THREE_ROLE_SYSTEM_PROMPT
from src.document_generation import setup_logger, logger
from pdf2image import convert_from_path
import requests


def make_claude_request_for_broken_sentences(payload: dict, pageno: str, english_texts_defragmented: dict) -> dict:

    headers = {
        "x-api-key": str(os.getenv("ANTHROPIC_API_KEY")),
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    model_name = "claude-3-5-sonnet-20241022"
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        json=payload,
        headers=headers
    )
    result = response.json()
    try:
        content = result['choices'][0]['message']['content']
        english_texts_defragmented[pageno] = re.search(r'<english_page_1_new_output>(.*?)</english_page_1_new_output>', 
                                                       content, re.DOTALL).group(1)
        return content
    except Exception as e:
        print(f"hey An Error occurred. Error details: {e}")
        print(re.search(r'<english_page_1(.*?)</english_page_1', content, re.DOTALL).group(1))
        ipdb.set_trace()
        return None


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
            "system": THREE_ROLE_SYSTEM_PROMPT,            
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": THREE_ROLE_USER_PROMPT
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
            "max_tokens": 5000,
            "temperature": 0.1
        }
        
        # Validate the constructed payload
        if not all(key in payload for key in ["model", "messages"]):
            raise ValueError("Payload missing required fields")
            
        return payload
        
    except Exception as e:
        logger.error(f"Error constructing payload: {str(e)}")
        raise


def construct_claude_payload_fragmented_sentences(
                        german_page_1: str,
                        german_page_2: str,
                        english_page_1_old_input: str,
                        german_page_1_top_fragment_to_be_ignored: str):
    
    print('construct_claude_payload_fragmented_sentences called')
    payload = {
        "model": "claude-3-5-sonnet-20241022",
        "system": FRAGMENTED_SENTENCES_SYSTEM_PROMPT, 
        "messages": [{
            "role": "user",
            "content": [{
                 "type": "text",
                "text": FRAGMENTED_SENTENCES_USER_PROMPT.format(
                    german_page_1=german_page_1,
                    german_page_2=german_page_2,
                    english_page_1_old_input=english_page_1_old_input,
                    german_page_1_top_fragment_to_be_ignored=german_page_1_top_fragment_to_be_ignored
                    )
                }]
            }],
        "max_tokens": 5000,
        "temperature": 0.1
        }

    return payload 


async def make_claude_request(base64_image: str) -> dict: 
    """
    Make an asynchronous request to the Anthropic API w/ built-in retries and error-handling.
    """

    model_name = "claude-3-5-sonnet-20241022"
    logger = logging.getLogger('logger_name')
    
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

