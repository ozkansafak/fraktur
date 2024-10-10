# pdf-processing/utils.py

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import logging

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
        plt.savefig(f'log_spectrum_{axis_name}.png')
        plt.close()

    return log_spectrum

def extract_image_bbox(log_spectrum: np.ndarray, axis_name: str = 'y', plotter: bool = False) -> tuple:
    """
    Extracts the bounding box coordinates from a log spectrum.

    Args:
        log_spectrum (np.ndarray): The log spectrum array.
        axis_name (str): The axis for bounding box extraction ('x' or 'y').
        plotter (bool): Whether or not to display the plot.

    Returns:
        tuple: The start and end coordinates of the bounding box.
    """
    axis = 0 if axis_name == 'y' else 1
    form = np.mean(log_spectrum, axis=axis) - np.mean(log_spectrum)
    n = len(form)

    lo, hi = None, None
    pad = 5
    for i in range(n):
        if lo is None and form[i] > 0 and all(form[i:i+5] > 0):
            lo = max(0, i-pad)
            if plotter:
                logging.debug(f'lo: {lo}')
            break

    for i in range(n-1, -1, -1):
        if hi is None and form[i] > 0 and all(form[i-4:i+1] > 0):
            hi = min(i+pad, len(form)-1)
            if plotter:
                logging.debug(f'hi: {hi}')
            break

    if plotter:
        s = {'X','Y'}.difference({axis_name}).pop() 
        plt.figure(figsize=(13, 2.2))
        plt.plot(form, 'k.-', alpha=.6)
        plt.plot(range(lo, hi+1), form[lo:hi+1], 'r.', alpha=1)
        plt.title(f"FFT-{axis_name}")
        plt.xlabel(f' {s}-axis')
        plt.xlim(0, len(form)-1)
        plt.savefig(f'fft_{axis_name}.png')
        plt.close()
        
    return lo, hi + 1
