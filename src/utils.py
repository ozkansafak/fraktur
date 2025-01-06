import time 
from PIL import Image
import logging
from io import BytesIO
import tiktoken
import base64
import sys, os, re, json
import matplotlib.pyplot as plt
import matplotlib.pylab as pylab
from typing import Dict, Tuple, List, Callable

# # Get the root path of the project
sys.path.append(os.path.abspath(".."))


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
        print(f"{func.__name__} runtime: {delta:.2f} sec")
    
        return result
    return wrapper

def setup_logger(name: str) -> logging.Logger:
    """Setup a simple logger that only outputs to stdout."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(funcName)s - L%(lineno)d - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
        
        # Don't propagate message to parent loggers
        logger.propagate = False 

    return logger

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

# Decorator to log wall time
def log_execution_time(func: Callable):
    logger = setup_logger('time_logger')
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        logger.info(f"Finished {func.__name__} in {time.time() - start:.2f} seconds.")
        return result
    return wrapper

def get_corresponding_bad_fnames(fnames, bad_pagenos):
    # get corresponding filenames in missing keys
    print('---' * 22)
    
    bad_fnames = []
    for fname in fnames:
        pageno = re.search(r'page_(.*?)\.pdf', fname, re.DOTALL).group(1)
        if pageno in bad_pagenos:
            bad_fnames.append(fname)
            
    for item in bad_fnames:
        print(f"bad_fnames: {item}") 
        
    return bad_fnames

def count_num_tokens(content: str, model_name: str = "gpt-4o-2024-08-06"):
    # Load the appropriate tokenizer for the model
    encoding = tiktoken.encoding_for_model(model_name)
    
    # Encode the prompt to count tokens
    tokens = encoding.encode(content)
    return len(tokens)

def delete_bad_pagenos(bad_pagenos, raw_german_texts, german_texts, english_texts):
    print('---' * 22)
    for pageno in bad_pagenos:
        print(f"> Deleting pageno:{pageno}")
        
        try:
            del raw_german_texts[pageno]
        except Exception as e:
            print("raw_german_texts. No key to delete", e)        
        
        try:
            del german_texts[pageno]
        except Exception as e:
            print("german_texts..... No key to delete", e)
            
        try:
            del english_texts[pageno]
        except Exception as e:
            print("english_texts.... No key to delete", e)

def find_bad_pagenos(all_pagenos, raw_german_texts, german_texts, english_texts, good_pagenos):
    bad_pagenos = []

    for pageno in all_pagenos:
        if pageno in good_pagenos:
            continue

        if pageno not in raw_german_texts:
            # check for missing <raw_german> -- i.e. missing key in raw_german_texts
            print(f'> pageno: {pageno}')
            bad_pagenos.append(pageno)
            continue

        if pageno in raw_german_texts:
            # check for unrequested summarization.
            for j, c in enumerate(raw_german_texts[pageno]):
                if c == '[':
                    print(f'> pageno: {pageno} in raw_german_texts:{raw_german_texts[pageno][j:j+100]} ...') 
                    bad_pagenos.append(pageno)
                    break
            if bad_pagenos and bad_pagenos[-1] == pageno:
                continue

        if pageno in english_texts:
            # check for unrequested summarization.
            for j, c in enumerate(english_texts[pageno]):
                if c == '[':
                    print(f'> pageno: {pageno} in english_texts:{english_texts[pageno][j:j+100]} ...') 
                    bad_pagenos.append(pageno)
                    break
            if bad_pagenos and bad_pagenos[-1] == pageno:
                continue
       
        if pageno in raw_german_texts and 'section was not found' in raw_german_texts[pageno]:
            bad_pagenos.append(pageno)
            print(f'> pageno: {pageno}. In raw_german_texts: {raw_german_texts[pageno]}')

        elif pageno in german_texts and 'section was not found' in german_texts[pageno]:
            bad_pagenos.append(pageno)
            print(f'> pageno: {pageno}. In german_texts: {german_texts[pageno]}')

        elif pageno in english_texts and 'section was not found' in english_texts[pageno]:
            bad_pagenos.append(pageno)
            print(f'> pageno: {pageno}. In english_texts: {english_texts[pageno]}')

        elif pageno not in english_texts:
            bad_pagenos.append(pageno)
            print(f'> pageno: {pageno}, pageno not in english_texts')

    print(f'\nbad_pagenos: {bad_pagenos}')
    return bad_pagenos

def dump_fragmented_output(foldername, english_texts_defragmented, fragments_2, contents):
    with open(f'../output_data/{foldername}/english_texts_defragmented.json', 'w') as f:
        json.dump(english_texts_defragmented, f)
    with open(f'../output_data/{foldername}/fragments_2.json', 'w') as f:
        json.dump(fragments_2, f)
    with open(f'../output_data/{foldername}/contents.json', 'w') as f:
        json.dump(contents, f)
    print(f'dumped fragemented outputs to foldername: {foldername}')
