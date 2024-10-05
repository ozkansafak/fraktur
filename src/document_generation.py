from docx import Document
import re

def create_docx(english_texts: dict, folder_name: str = '', language: str = 'English') -> None:
    """
    Creates a .docx document from a dictionary of English texts.

    Args:
        english_texts (dict): A dictionary where keys are page numbers and values are English text.
        folder_name (str): The folder name to save the document.
        language (str): The file name for the document ('English' or 'German')

    Returns:
        None
    """
    document = Document()
    for page in sorted(english_texts.keys()):
        text = english_texts[page]
        text = re.sub(r'\n+', '\n', text)
        document.add_heading(f"Page {page}", level=1)
        document.add_paragraph(text)

    document.save(f'output/{folder_name}/{language}.docx')

