
import requests
import json
import re

"""Simplified module for interacting with the LLM API using only port, fixed JSON header, and JSON payload."""

API_HEADER = {"Content-Type": "application/json"}

def infer(payload: dict, port: int = 6000) -> dict:
    """
    Send a JSON payload to the LLM API and return the response.
    Args:
        payload (dict): The inference payload.
        port (int): The port for the API endpoint.
    Returns:
        dict: The model's response.
    """
    url = f"http://localhost:{port}/v1/chat/completions"
    try:
        response = requests.post(url, headers=API_HEADER, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise RuntimeError(f"Inference failed: {e}")

def getTokenCount(text: str, port: int = 6000) -> int:
    """
    Send a POST request to the /tokenize endpoint to get the token count for the given text.
    Args:
        text (str): The text to tokenize.
        port (int): The port for the API endpoint.
    Returns:
        int: The number of tokens in the text.
    """
    url = f"http://localhost:{port}/tokenize"
    payload = {
        "content": text,
        "add_special": True,
        "parse_special": True,
        "with_pieces": True
    }
    try:
        response = requests.post(url, headers=API_HEADER, json=payload)
        response.raise_for_status()
        data = response.json()
        tokens = data.get("tokens", [])
        return len(tokens)
    except Exception as e:
        raise RuntimeError(f"Token count request failed: {e}")


def extract_article_metadata(pages: list[str], port: int = 6000) -> dict:
    """
    Extracts metadata from a list of page texts using the local LLM.
    
    Args:
        pages (list[str]): A list where each string represents the text of one page.
        port (int): The port of the running llama.cpp server.
        
    Returns:
        dict: The extracted metadata in JSON format, or None if failed.
    """
    
    # 1. Validation & Pre-processing
    if not pages or all(not p.strip() for p in pages):
        print("Warning: Received empty page list.")
        return None

    # We only need the first 2 pages for metadata (Title, Abstract, Authors usually appear here).
    # Joining with a separator helps the model understand page breaks, though not strictly necessary.
    joined_text = "\n--- PAGE BREAK ---\n".join(pages[:2])
    
    # Truncate to ~1500 tokens (approx 4000-5000 chars) to keep CPU inference fast
    # and prevent context window overflow.
    clean_text = joined_text[:4500].replace('"', "'").replace("\\", "")

    # 2. Define the Prompt
    system_instruction = (
        "You are an expert bibliometric assistant specialized in Arabic academic texts. "
        "You strictly output valid JSON with no markdown formatting or conversational text."
    )

    user_prompt = f"""
    Analyze the following academic text (from the first two pages) and extract the metadata into a JSON object.

    ### TARGET JSON SCHEMA:
    {{
      "title": "string (Exact title found in text)",
      "abstract_ar": "string (The Arabic abstract text)",
      "general_field": "string (Broad category e.g. Economics, Law, Engineering)",
      "field": "string (Specific topic e.g. Macroeconomics, Civil Law)",
      "authors": ["string", "string"],
      "publish_date": "YYYY-MM-DD (or null)"
    }}

    ### EXTRACTION RULES:
    1. **Authors**: Extract names only. Remove titles like "Dr.", "Prof.", "أ.د", "دكتور".
    2. **Dates**: Convert dates to ISO 8601 (YYYY-MM-DD). If only the year is found (e.g., 2022), use "2022-01-01".
    3. **Missing Data**: If a field is not found, set it to null.
    4. **Language**: Keep 'title' and 'abstract_ar' in their original language (usually Arabic). 'general_field' and 'field' should be in English.

    ### INPUT TEXT:
    \"\"\"
    {clean_text}
    \"\"\"
    """

    # 3. Construct Payload
    payload = {
        "model": "/models/Qwen2.5-7B-Instruct-Q4_K_M.gguf", # Ensure this matches your container path
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,    # Low temp for factual extraction
        "max_tokens": 1024,    # Enough for abstract + metadata
        "stream": False
    }

    # 4. Call Inference
    try:
        response_data = infer(payload, port=port)
        content = response_data['choices'][0]['message']['content']

        # 5. Parse and Clean Response
        # Regex to extract JSON block in case the model adds "Here is your JSON:" chatter
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        
        if json_match:
            clean_json_str = json_match.group(0)
            return json.loads(clean_json_str)
        else:
            # Fallback: try parsing the whole string
            return json.loads(content)

    except json.JSONDecodeError:
        print(f"Error: Model output was not valid JSON.\nRaw Output: {content}")
        return None
    except Exception as e:
        print(f"Error during extraction: {e}")
        return None