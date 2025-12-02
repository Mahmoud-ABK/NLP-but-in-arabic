import pytesseract
from pdf2image import convert_from_path
import json
import os
from PyPDF2 import PdfReader

def extract_first_three_pages(pdf_path):
    """
    Extracts the first three pages of a PDF and returns a JSON object.
    Uses OCR only if no text is found via direct extraction.

    Args:
        pdf_path (str): path to the PDF file.

    Returns:
        dict: JSON object with the content of the first three pages.
    """
    extracted_text = {}
    try:
        reader = PdfReader(pdf_path)
        for i in range(min(3, len(reader.pages))):
            page_obj = reader.pages[i]
            text = page_obj.extract_text()
            if text and text.strip():
                extracted_text[f"page{i+1}"] = text.strip()
            else:
                # Fallback to OCR for this page
                pages = convert_from_path(pdf_path, dpi=300, first_page=i+1, last_page=i+1)
                ocr_text = pytesseract.image_to_string(pages[0], lang="ara+eng")
                extracted_text[f"page{i+1}"] = ocr_text.strip()
    except Exception as e:
        # If direct extraction fails, fallback to OCR for all
        pages = convert_from_path(pdf_path, dpi=300)
        for i, page in enumerate(pages[:3], start=1):
            page_text = pytesseract.image_to_string(page, lang="ara+eng")
            extracted_text[f"page{i}"] = page_text.strip()

    return extracted_text

def extract_first_two_pages_ocr(pdf_path):
    """
    Extracts the first two pages of a PDF using OCR only.
    
    Args:
        pdf_path (str): path to the PDF file.

    Returns:
        dict: JSON object with the OCR content of the first two pages.
    """
    extracted_text = {}
    try:
        pages = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=2)
        for i, page in enumerate(pages, start=1):
            ocr_text = pytesseract.image_to_string(page, lang="ara+eng")
            extracted_text[f"page{i}"] = ocr_text.strip()
    except Exception as e:
        extracted_text["error"] = str(e)
    return extracted_text
if __name__ == "__main__":
    # Path to a sample PDF in the finalpdfs directory
    
    sample_pdf_path = os.path.join(os.path.dirname(__file__), "../finalpdfs/1.pdf")

    # Check if the sample PDF exists
    if not os.path.exists(sample_pdf_path):
        print(f"Sample PDF not found at {sample_pdf_path}")
    else:
        # Extract the first three pages
        extracted_content = extract_first_two_pages_ocr(sample_pdf_path)

        # Print the extracted content
        print("Extracted content from the first three pages:")
        print(json.dumps(extracted_content, indent=4, ensure_ascii=False))

