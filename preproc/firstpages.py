import pytesseract
from pdf2image import convert_from_path
import json

def extract_first_three_pages(pdf_path):
    """
    extracts the first three pages of a pdf and returns a json object.

    args:
        pdf_path (str): path to the pdf file.

    returns:
        dict: json object with the content of the first three pages.
    """
    # convert pdf pages to images
    pages = convert_from_path(pdf_path, dpi=300)

    # ocr both arabic and english
    lang = "ara+eng"

    # extract text from the first three pages
    extracted_text = {}
    for i, page in enumerate(pages[:3], start=1):
        page_text = pytesseract.image_to_string(page, lang=lang)
        extracted_text[f"page{i}"] = page_text.strip()

    return extracted_text

