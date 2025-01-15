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
from src.api_requests_claude import make_claude_request
from pdf2image import convert_from_path
from src.constants import THREE_ROLE_USER_PROMPT, THREE_ROLE_SYSTEM_PROMPT
from src.document_generation import setup_logger, logger
import requests



def construct_payload_for_gpt(base64_image: str) -> dict:
    """
    Constructs the payload for the GPT-4o model with a base64 encoded image.

    Args:
        base64_image (str): The base64 encoded image string.

    Returns:
        dict: The constructed payload for the API request.
    """
    model_name = "gpt-4o-2024-08-06"
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "system", 
                "content": THREE_ROLE_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": THREE_ROLE_USER_PROMPT
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
        "max_tokens": 5000,
        "temperature": 0.1
    }

    return payload

def construct_gpt_payload_fragmented_sentences(
                        german_page_1: str,
                        german_page_2: str,
                        english_page_1_old_input: str,
                        german_page_1_top_fragment_to_be_ignored: str):

    print('construct_gpt_payload_fragmented_sentences called')
    payload = {
        "model": "gpt-4o-2024-08-06",
        "messages": [
            {
                "role": "system",
                "content": FRAGMENTED_SENTENCES_SYSTEM_PROMPT
            },
            {
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
            },
        ],
        "max_tokens": 5000,
        "temperature": 0.1
    }

    return payload 


async def make_gpt_request(base64_image: str) -> dict:
    """ Asynchronous version of send_gpt_request """
    # logger.info(f"In make_gpt_request, model_name: gpt-4o-2024-08-06")
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.openai.com/v1/chat/completions",
            json=construct_payload_for_gpt(base64_image),
            headers=headers
        ) as response:
            return await response.json()

def make_gpt_request_for_broken_sentences(payload: dict, pageno: str, english_texts_defragmented: dict) -> dict:

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}"
    }

    model_name = "gpt-4o-2024-08-06"
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
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


