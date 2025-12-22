from utils.qwen import extract_article_metadata , infer
import pandas as pd
import numpy as np

def process_row(row: pd.Series,port=6000,host="localhost") -> pd.Series:
    """
    Validates and merges metadata extracted by Qwen with the existing row data.
    Prioritizes existing row content in case of conflicts.
    """
    
    # 1. Perform the extraction
    # Assuming extract_article_metadata takes the row or a specific field like 'page1'
    # Adjust the input argument based on your actual extract_article_metadata signature
    extracted_data = extract_article_metadata(row["page1"],row["page2"],port,host)
    
    # 2. Create a copy of the row to update
    updated_row = row.copy()
    
    # Keys returned by the extraction function
    target_keys = ['title', 'abstract_ar', 'general_field', 'authors', 'keywords', 'publish_date']
    
    for key in target_keys:
        row_value = row.get(key)
        extracted_value = extracted_data.get(key)
        
        # Check if the row value is effectively "empty" 
        # (Handles None, NaN, empty strings, or empty lists)
        is_row_empty = (
            pd.isna(row_value) or 
            (isinstance(row_value, str) and row_value.strip() == "") or
            (isinstance(row_value, list) and len(row_value) == 0)
        )
        
        if is_row_empty:
            # If the row is empty, fill it with the extracted value
            updated_row[key] = extracted_value
        else:
            # If the row has content, prioritize it (already there)
            # You can optionally add validation logic here if the values differ significantly
            pass
            
    return updated_row


import json
import re

import json
import re

def fix_authors(authors_ar_str: str, authors_en_str: str = "", port: int = 6000) -> list:
    """
    Corrects Arabic names using Latin as phonetic ground truth.
    """
    if not authors_ar_str or not authors_ar_str.strip():
        return []

    system_instruction = "You are an expert in Arabic bibliometrics and OCR name correction."
    
    user_prompt = f"""
    Refine and correct the following author names.

    INPUT LATIN : "{authors_en_str}"
    INPUT ARABIC : "{authors_ar_str}"

    INSTRUCTIONS:
    1. fix the arabic name 
    2. **Noise**: Remove all titles (Dr, Prof, أ.د) and symbols ($, #, *).
    3. **Missing Latin**: If no Latin exists for an Arabic name, generate a standard transliteration.
    4. **Output**: Return ONLY a JSON array of objects.

    FORMAT:
    [
      {{"latin": "Latin Name" ,"ar": "Corrected Arabic Name" }}
    ]
    """

    payload = {
        "model": "/models/Qwen2.5-7B-Instruct-Q4_K_M.gguf",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7, # Keep it low for high fidelity
        "stream": False,
        "response_format": {"type": "json_object"}
    }

    try:
        response_data = infer(payload, port=port) # Assuming infer() is defined elsewhere
        content = response_data['choices'][0]['message']['content']
        return content
    except Exception as e:
        print(f"Error: {e}")
        return []

def get_fixed_authors(row, port: int = 6000):
    """
    Processes a row. Returns (Arabic List, Latin List).
    If original Latin was present, it prioritizes the LLM's corrected version of it.
    """
    ar_raw = str(row['authors']) if pd.notna(row['authors']) else ""
    en_raw = str(row['authors_en']) if pd.notna(row['authors_en']) else ""

    # Get the cleaned/corrected results from LLM
    # Results look like: [{"ar": "جمال", "latin": "Jamal"}, ...]
    refined_results = fix_authors(ar_raw, en_raw, port=port)

    if not refined_results:
        # Fallback if LLM returns nothing
        return pd.Series([[], []])

    # Extract lists
    authors_ar = [item.get("ar", "").strip() for item in refined_results]
    authors_en = [item.get("latin", "").strip() for item in refined_results]

    # Note: Since the prompt already uses en_raw as "ground truth", 
    # version of your original string.
    if en_raw != "" : 
        authors_en = en_raw
    return pd.Series([authors_ar, authors_en])