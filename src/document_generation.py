from fpdf import FPDF
from docx import Document
import re

# def save_document(english_texts: dict, folder_name: str = '', language: str = 'English') -> None:
#     """
#     Creates a .docx document from a dictionary of English texts.

#     Args:
#         english_texts (dict): A dictionary where keys are page numbers and values are English text.
#         folder_name (str): The folder name to save the document.
#         language (str): The file name for the document ('English' or 'German')

#     Returns:
#         None
#     """
#     document = Document()
#     for pageno in sorted(english_texts.keys()):
#         text = english_texts[pageno]
#         text = re.sub(r'\n+', '\n', text)

#         # Add page number
#         document.add_heading(f"Page {pageno}", level=1)

#         # Extract header
#         header = re.search(r'<header>(.*?)</header>', text, re.DOTALL)
#         if header is not None: 
#             document.add_heading(header.group(1), level=1) 

#         # Extract body
#         body = re.search(r'<body>(.*?)</body>', text, re.DOTALL).group(1)
#         for paragraph in body.split('\n'):
#             document.add_paragraph(paragraph)

#         # Extract footnotes
#         footer = re.search(r'<footer>(.*?)</footer>', text, re.DOTALL)
#         if footer is not None: 
#             document.add_heading(footer.group(1), level=2) 

#     # save as docx first
#     fname = f'../output/{folder_name}/{language}'
#     document.save(f'{fname}.docx')

from docx import Document
from docx.shared import Pt
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re

from docx import Document
from docx.shared import Pt
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re

from docx import Document
from docx.shared import Pt
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import re

def add_bottom_border(paragraph, border_size='1', border_color='auto', border_space='1', border_val='single'):
    """
    Adds a bottom border to a paragraph by modifying its XML properties.

    Args:
        paragraph: The paragraph to which the border will be added.
        border_size: The size (thickness) of the border in eighths of a point.
        border_color: The color of the border (e.g., 'auto' for automatic/black).
        border_space: The space between the border and the text.
        border_val: The style of the border (e.g., 'single', 'double', 'dashed').
    """
    p = paragraph._p  # Get the XML element of the paragraph
    pPr = p.get_or_add_pPr()
    borders = pPr.find(qn('w:pBdr'))
    if borders is None:
        borders = OxmlElement('w:pBdr')
        pPr.append(borders)
    bottom_border = OxmlElement('w:bottom')
    bottom_border.set(qn('w:val'), border_val)
    bottom_border.set(qn('w:sz'), border_size)
    bottom_border.set(qn('w:space'), border_space)
    bottom_border.set(qn('w:color'), border_color)
    borders.append(bottom_border)

def save_document(english_texts: dict, folder_name: str = '', language: str = 'English') -> None:
    """
    Creates a .docx document from a dictionary of texts, adds a footer with a smaller font size than the header,
    and inserts a horizontal line between the body and the footer.

    Args:
        english_texts (dict): A dictionary where keys are page numbers and values are text.
        folder_name (str): The folder name to save the document.
        language (str): The file name for the document ('English' or 'German').

    Returns:
        None
    """
    document = Document()
    
    # Add and customize the header and footer
    section = document.sections[0]
    
    # Add header
    header = section.header
    header_paragraph = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    # header_run = header_paragraph.add_run("Document Header")
    # header_run.font.size = Pt(16)  # Header font size
    
    # Add footer
    footer = section.footer
    footer_paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    footer_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER  # Center alignment

    # Clear existing runs in footer paragraph
    footer_paragraph.clear()

    # Add page number to footer
    page_run = footer_paragraph.add_run()
    page_run.font.size = Pt(10)  # Footer font size

    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')

    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = 'PAGE'

    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'end')

    page_run._r.append(fldChar1)
    page_run._r.append(instrText)
    page_run._r.append(fldChar2)

    # Create a footnote style
    styles = document.styles
    if 'FootnoteStyle' not in styles:
        footnote_style = styles.add_style('FootnoteStyle', WD_STYLE_TYPE.PARAGRAPH)
        footnote_style.font.size = Pt(10)  # Footnote font size
    else:
        footnote_style = styles['FootnoteStyle']
    
    for pageno in sorted(english_texts.keys()):
        text = english_texts[pageno]
        text = re.sub(r'\n+', '\n', text)

        # Add page number as a heading
        document.add_heading(f"Page {pageno}", level=1)

        # Extract header
        header_match = re.search(r'<header>(.*?)</header>', text, re.DOTALL)
        if header_match is not None: 
            header_text = header_match.group(1)
            document.add_heading(header_text, level=1) 
            # Create an empty paragraph, then add bottom border to the paragraph
            hr_paragraph = document.add_paragraph()
            add_bottom_border(hr_paragraph, border_size='2', border_color='auto', border_space='1', border_val='single')

        # Extract body
        body_match = re.search(r'<body>(.*?)</body>', text, re.DOTALL)
        if body_match:
            body = body_match.group(1)
            for paragraph in body.split('\n'):
                document.add_paragraph(paragraph)
        
        # Extract footnotes
        footer_match = re.search(r'<footer>(.*?)</footer>', text, re.DOTALL)
        if footer_match is not None: 
            # First, add a horizontal line between body and footer
            # Create an empty paragraph, then add bottom border to the paragraph
            hr_paragraph = document.add_paragraph()
            add_bottom_border(hr_paragraph, border_size='2', border_color='auto', border_space='1', border_val='single')

            footer_text = footer_match.group(1)
            # Add footnotes with the footnote style
            for footnote in footer_text.split('\n'):
                footnote_paragraph = document.add_paragraph(footnote)
                footnote_paragraph.style = footnote_style

    # Save the document
    fname = f'../output/{folder_name}/{language}'
    document.save(f'{fname}.docx')
