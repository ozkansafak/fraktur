from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
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
    Creates a .docx document from a dictionary of texts, adds a header and footer with dynamic page numbers,
    and inserts a horizontal line between the body and the footer.
    """
    document = Document()

    styles = document.styles
    if 'CustomHeaderStyle' not in styles:
        custom_style = styles.add_style('CustomHeaderStyle', WD_STYLE_TYPE.PARAGRAPH)
        custom_style.font.name = 'Arial'
        custom_style.font.size = Pt(10)
        custom_style.font.color.rgb = RGBColor(0, 0, 0)
        custom_style.font.bold = False
        custom_style.font.italic = False
    else:
        custom_style = styles['CustomHeaderStyle']

    # Add and customize the header and footer
    section = document.sections[0]
    
    # Configure Header
    header = section.header
    header_paragraph = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    header_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER  # Center alignment
    header_paragraph.clear()

    # Configure Footer 
    footer = section.footer
    footer_paragraph = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    footer_paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER  # Center alignment

    # Create a footnote style
    styles = document.styles
    if 'FootnoteStyle' not in styles:
        footnote_style = styles.add_style('FootnoteStyle', WD_STYLE_TYPE.PARAGRAPH)
        footnote_style.font.size = Pt(9)  # Footnote font size
    else:
        footnote_style = styles['FootnoteStyle']
        
    for index, pageno in enumerate(sorted(english_texts.keys())):
        text = english_texts[pageno]
        text = re.sub(r'\n+', '\n', text)
    
        # Insert a page break before each new page except the first
        if index > 0:
            document.add_page_break()

        # Extract header
        header_match = re.search(r'<header>(.*?)</header>', text, re.DOTALL)
        if header_match is None:
            header_text = ""
        else:
            header_text = header_match.group(1)
        header_text = f"Page {pageno}\n{header_text}"

        # Add header text as a heading in the body
        header_paragraph = document.add_heading(header_text)
        header_paragraph.style = custom_style

        for run in header_paragraph.runs:
            run.font.size = Pt(14)
            run.font.color.rgb = RGBColor(0, 0, 0)
        
        # Add a bottom border after the header
        hr_paragraph = document.add_paragraph()
        add_bottom_border(hr_paragraph, border_size='2', border_color='auto', border_space='1', border_val='single')

        # Extract body
        body_match = re.search(r'<body>(.*?)</body>', text, re.DOTALL)
        if body_match:
            body = body_match.group(1)
            for paragraph in body.split('\n'):
                paragraph = document.add_paragraph(paragraph)
                paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY

        
        # Extract footnotes
        footer_match = re.search(r'<footer>(.*?)</footer>', text, re.DOTALL)
        if footer_match is not None:
            footer_text = footer_match.group(1)
            # Add a horizontal line between body and footnotes
            hr_paragraph = document.add_paragraph()
            add_bottom_border(hr_paragraph, border_size='2', border_color='auto', border_space='1', border_val='single')
            # Add footnotes with the footnote style
            footnote_paragraph = document.add_paragraph(footer_text)
            footnote_paragraph.style = footnote_style
    
    # Save the document
    fname = f'../output/{folder_name}/{language}'
    document.save(f'{fname}.docx')

    return document, fname
