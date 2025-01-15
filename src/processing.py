from PIL import Image
import numpy as np
from typing import Dict, Tuple, List
import re
import matplotlib.pyplot as plt
from src.document_generation import setup_logger, logger
from src.utils import pylab, plt, encode_image, log_execution_time, count_num_tokens
from src.api_requests_gpt import make_gpt_request
from src.api_requests_claude import make_claude_request
from pdf2image import convert_from_path


def compute_log_spectrum_1d(arr: np.ndarray, axis: int, plotter: bool = False) -> np.ndarray:
    """
    Computes the log spectrum along one axis (X or Y).

    Args:
        arr (np.ndarray): ndarray representation of the image.
        axis (int): Axis along which to compute FFT. (0 for Y-axis, 1 for X-axis)
        plotter (bool): Whether or not to display plots.

    Returns:
        np.ndarray: log spectrum along the specified axis.
    """
    
    # Convert to 2D grayscale by reducing across the color channels
    image_2d = np.mean(arr, axis=2)
    
    # Subtract mean along the X or Y axes
    if axis == 0:  # Y-axis FFT (along columns)
        meany = np.mean(image_2d, axis=0)
        image_2d -= meany
    else:  # X-axis FFT (along rows)
        meanx = np.mean(image_2d, axis=1)
        image_2d -= meanx[:, np.newaxis]

    # Compute 1D FFT along the specified axis
    if axis == 0:  # FFT along Y (columns)
        fft_result = np.array([np.fft.fft(image_2d[:, i]) for i in range(image_2d.shape[1])]).T
    else:  # FFT along X (rows)
        fft_result = np.array([np.fft.fft(image_2d[i]) for i in range(image_2d.shape[0])])

    # Compute log energy spectrum (log squared FFT)
    log_spectrum = np.log(np.abs(fft_result) ** 2 + 1)

    # Plot heatmap
    if plotter:
        plt.figure(figsize=(6, 3.5))
        axis_name = 'X' if axis == 1 else 'Y'
        plt.imshow(log_spectrum, aspect='equal', cmap='hot')
        plt.colorbar(label='Log Energy Spectrum')
        plt.title(f'Log Energy Spectrum Along {axis_name}-axis')
        plt.xlabel(f'{axis_name}-axis')
        plt.ylabel(f'Frequency ({axis_name}-axis)')
        plt.gca().axis('off')
        plt.show()

    return log_spectrum

def extract_image_bbox(log_spectrum: np.ndarray, 
                       axis_name: str = 'y', 
                       plotter: bool = False) -> tuple:
    """
    Extracts the bounding box coordinates from a log spectrum.

    Args:
        log_spectrum (np.ndarray): The log spectrum array.
        axis (str): The axis for bounding box extraction ('x' or 'y').
        plotter (bool): Whether or not to display the plot.

    Returns:
        tuple: The start and end coordinates of the bounding box.
    """
    axis = 0 if axis_name == 'y' else 1
    form = np.mean(log_spectrum, axis=axis) - np.mean(log_spectrum)
    n = len(form)
    
    lo, hi = None, None
    pad = 10
    for i in range(n):
        if lo is None and form[i] > 0 and all(form[i:i+5] > 0):
            lo = max(0, i-pad)
            if plotter:
                print('lo:', lo)
            break

    for i in range(n-1, -1, -1):
        if hi is None and form[i] > 0 and all(form[i-4:i+1] > 0):
            hi = min(i+pad, len(form)-1)
            if plotter:
                print('hi:', hi)
            break

    if plotter:
        s = {'X','Y'}.difference({axis_name}).pop()
        plt.figure(figsize=(13, 2.2))
        plt.plot(form, 'k.-', alpha=.6)
        plt.plot(range(lo, hi+1), form[lo:hi+1], 'r.', alpha=1)
        plt.title(f"FFT-{axis_name}")
        plt.xlabel(f' {s}-axis')
        plt.xlim(0, len(form)-1)
        plt.show()
        
    return lo, hi + 1

def save_images(y_lo: int, y_hi: int, x_lo: int, x_hi: int, arr: np.ndarray, pageno: int) -> None:
    """
    Saves the original and cropped images for the input numpy array representation of an Image.

    Args:
        y_lo (int): top Y-axis coordinate of bounding box.
        y_hi (int): bottom Y-axis coordinate of bounding box.
        x_lo (int): Lower X-axis coordinate of bounding box.
        x_hi (int): Upper X-axis coordinate of bounding box.
        arr (np.ndarray): The image array.
        pageno (int): The page number.

    Returns:
        None
    """
    fig = plt.figure(figsize=(15,15))
    image = Image.fromarray(arr[y_lo:y_hi, x_lo:x_hi])
    plt.imshow(image)
    plt.gca().axis('off')
    plt.savefig(f'../figures/{pageno}_cropped.png', bbox_inches='tight')

    plt.imshow(image)
    plt.gca().axis('off')
    image = Image.fromarray(arr)
    plt.imshow(image)
    plt.gca().axis('off')
    plt.savefig(f'../figures/{pageno}.png', bbox_inches='tight')
    plt.close(fig)


async def process_single_page(fname: str, model_name: str, plotter: bool, pageno: str, extract: bool = True) -> Tuple[str, str, str, str]:
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
        response_dict = await make_gpt_request(base64_image)
    else:
        response_dict = await make_claude_request(base64_image)

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
    token_count = count_num_tokens(content)

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

    return content, token_count, raw_german_text, german_text, english_text

def extract_text_section(pageno: str, content: str, section: str) -> str:
    """Helper function to extract text sections with error handling"""
    
    logger = setup_logger('extract_text_section')
    
    match = re.search(f'<{section}>(.*?)</{section}>', content, re.DOTALL)
    if match is None:
        logger.error(f'pageno: {pageno}, section name:"{section}" was not found. token_count={count_num_tokens(content)}')
        return f'pageno: {pageno}, "<{section}>" section was not found'
    return match.group(1)

async def process_single_page(fname: str, model_name: str, plotter: bool, pageno: str, extract: bool = True) -> Tuple[str, str, str, str]:
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
        response_dict = await make_gpt_request(base64_image)
    else:
        response_dict = await make_claude_request(base64_image)

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
    token_count = count_num_tokens(content)

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

    return content, token_count, raw_german_text, german_text, english_text


def extract_text_section(pageno: str, content: str, section: str) -> str:
    """Helper function to extract text sections with error handling"""
    
    logger = setup_logger('extract_text_section')
    
    match = re.search(f'<{section}>(.*?)</{section}>', content, re.DOTALL)
    if match is None:
        logger.error(f'pageno: {pageno}, section name:"{section}" was not found. token_count={count_num_tokens(content)}')
        return f'pageno: {pageno}, "<{section}>" section was not found'
    return match.group(1)
