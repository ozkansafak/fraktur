from docx import Document
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Inches
import re
import logging
from dataclasses import dataclass
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger('logger_name')
logger.setLevel(logging.INFO)


def setup_logger(name: str) -> logging.Logger:
    """Setup a simple logger that only outputs to stdout."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
    
    return logger

def strip_newlines(text: str) -> str:
    """Clean text by removing newlines adjacent to section tags."""
    # Remove \n before and after section tags
    text = re.sub(r'\n*<(body|header|footer)>', r'<\1>', text)
    text = re.sub(r'</(body|header|footer)>\n*', r'</\1>', text)
    
    return text

def extract_sections_in_order(text: str) -> list:
    """
    Extracts sections in the order they appear in the text.
    
    Args:
        text (str): Text containing header, body, and footer tags
        
    Returns:
        list: List of tuples (section_type, section_content) in order of appearance
    """
    # Pattern to match any section
    pattern = r'<(header|body|footer)>(.*?)</\1>'
    
    # Find all sections in order of appearance
    sections = []
    for match in re.finditer(pattern, text, re.DOTALL):
        section_type = match.group(1)
        content = match.group(2)
        sections.append((section_type, content))
    
    return sections

def add_bottom_border(paragraph: Any) -> None:
    """Adds a bottom border to a paragraph."""
    p = paragraph._p
    pPr = p.get_or_add_pPr()
    borders = pPr.find(qn('w:pBdr'))
    if borders is None:
        borders = OxmlElement('w:pBdr')
        pPr.append(borders)
    bottom_border = OxmlElement('w:bottom')
    bottom_border.set(qn('w:val'), 'single')
    bottom_border.set(qn('w:sz'), '2')
    bottom_border.set(qn('w:space'), '1')
    bottom_border.set(qn('w:color'), 'auto')
    borders.append(bottom_border)

def setup_document_styles(document: Document) -> Dict[str, Any]:
    """Sets up document styles and returns them."""
    styles = document.styles

    # Header style
    if 'CustomHeaderStyle' not in styles:
        header_style = styles.add_style('CustomHeaderStyle', WD_STYLE_TYPE.PARAGRAPH)
        header_style.font.name = 'Arial'
        header_style.font.size = Pt(14)
        header_style.font.color.rgb = RGBColor(0, 0, 0)

    # Footnote style
    if 'FootnoteStyle' not in styles:
        footnote_style = styles.add_style('FootnoteStyle', WD_STYLE_TYPE.PARAGRAPH)
        footnote_style.font.size = Pt(9)

    return {
        'header': styles['CustomHeaderStyle'],
        'footnote': styles['FootnoteStyle']
    }

def save_document(texts: dict, 
                  folder_name: str = '', 
                  language: str = 'English') -> Tuple[Document, str]:
    """
    Creates a .docx document maintaining the original section order.
    """
    logger = setup_logger('ocr_processor')

    document = Document()
    styles = setup_document_styles(document)

    # Configure document margins
    section = document.sections[0]
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    # Process each page
    for index, pageno in enumerate(sorted(texts.keys())):
        text = re.sub(r'\n+', '\n', texts[pageno])
        
        text = strip_newlines(text)
        
        # Add page break for all pages except the first
        if index > 0:
            document.add_page_break()

        # Get sections in their original order
        sections = extract_sections_in_order(text)

        # add page number
        header_para = document.add_paragraph(f"Page {pageno}\n")
        header_para.style = styles['header']
        header_para.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

        for section_type, content in sections:
            if section_type == 'header':
                # Add page number to header content
                header_para = document.add_paragraph(content)
                header_para.style = styles['header']
                header_para.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT

            elif section_type == 'body':
                # Add body paragraphs
                for para_text in content.split('\n'):
                    if para_text.strip():
                        body_para = document.add_paragraph(para_text)
                        body_para.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY

            elif section_type == 'footer':
                # Add border paragraph before footer
                border_para = document.add_paragraph()
                add_bottom_border(border_para)

                # Add footer content
                footer_para = document.add_paragraph(content)
                footer_para.style = styles['footnote']
                footer_para.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY

    # Save the document
    fname = f'../output_data/{folder_name}/{language}'
    document.save(f'{fname}.docx')

    return document, fname
