## Fraktur typeface German pdf document -> English

This repository provides a comprehensive pipeline that automates the extraction of text from PDF images of German documents written in Fraktur font, translates the text into English, and generates a .docx Word document for the original German transcription and its English translation.

## Overview
The pipeline consists of three main components:

1. Image Preprocessing and Cropping
2. API Request to GPT-4o
3.  `.docx` Document Generation

**1. Image Preprocessing and Cropping**

We perform a Discrete Fourier Transform (FFT) independently in the X and Y directions to analyze the frequency components of the image and identify the boundaries of text blocks.

Using Discrete Fourier Transform (FFT) on the image, we perform FFT in X and Y directions idependently to identify the boundaries of the text excluding the sporadic line notes and margins of the scanned image of the page. By sending smaller images to the API, the we reduce the API usage costs, data transfer times are improved,  cropping enhances the model's ability to focus on relevant text. 

**2.  API Request to GPT-4o**

GPT-4o performs three separate subtasks in succession. 
1.  Encode the image and send it to GPT-4o endpoint to get an OCR'ed raw German text.
2.  Re-evaluate the transcription to identify the header, the body and the footnotes on the page. 
3.  Translate the German text into English, while staying loyal to the original format, and the style of the text.

**3. `.docx` Document Generation**

The English text is converted into a .docx file which can later be converted into a pdf, if needed. 


<div align="center">
  <img src="output/readme figures/456.png" alt="Original Image" style="height: 400px; object-fit: contain;">
  <p>Fig 1. Original image provided in pdf format.</p>
</div>


<div align="center">
  <img src="output/readme figures/FFT-y heatmap.png" alt="FFT-x Form" style="height: 200px; object-fit: contain;">
  <img src="output/readme figures/FFT-x heatmap.png" alt="FFT-x Form" style="height: 200px; object-fit: contain;">
  
  <p>Fig 2. (a) log energy spectrum of image in Y-dir. Notice, the right and left margins are evident from the picture and left and right boundaries of the text area are evident.<br>
  (b) log energy spectrum of partially cropped image in X-dir. </p>
</div>

<div align="center">
  <img src="output/readme figures/FFT-x form.png" alt="FFT-x Form" style="height: 200px; object-fit: contain;">
  <img src="output/readme figures/FFT-y form.png" alt="FFT-x Form" style="height: 200px; object-fit: contain;">

  <p>Fig 3. (a) the mean log-energy spectrum in x-dir, and mean taken in y-dir  <br>
  (b) the mean log-energy spectrum in y-dir, and mean taken in x-dir</p>
</div>


<div align="center">
  <img src="output/readme figures/456_cropped.png" alt="Cropped Image" style="height: 260px; object-fit: contain;">

  <p>Fig 4.  Output: the cropped image</p>
</div>
<br>



<div align="center">
  <img src="output/readme figures/German 456.png" alt="Cropped Image" style="height: 300px; object-fit: contain;">

  <p>Fig 4.  German Transcription of original Fraktur document </p>
</div>
<br>


<div align="center">
  <img src="output/readme figures/English 456.png" alt="Cropped Image" style="height: 300px; object-fit: contain;">

  <p>Fig 4.  English Translation of the German document</p>
</div>

