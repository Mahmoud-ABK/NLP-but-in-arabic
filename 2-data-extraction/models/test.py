import requests

url = "http://localhost:6000/v1/chat/completions"

payload = {
    "model": "qwen-extractor-1",   # must match LLAMA_ARG_ALIAS
    "messages": [
        {"role": "user", "content": "Hello! Can you help me with data extraction?"}
    ]
}

response = requests.post(url, json=payload, timeout=60)
print("Status:", response.status_code)
print("Response:")
print(response.json())
