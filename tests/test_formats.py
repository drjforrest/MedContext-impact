#!/usr/bin/env python3
"""Test different payload formats for the HF endpoint."""
import base64
import httpx
import json
import os

# Simple 1x1 test image
test_image = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "8900000010494441541863f8cfc0f0030000050002fef02cc0890000000049454e"
    "44ae426082"
)

url = os.getenv("MEDGEMMA_ENDPOINT_URL", "https://your-endpoint-url.endpoints.huggingface.cloud")
token = os.getenv("MEDGEMMA_HF_TOKEN", "your_token_here")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

encoded = base64.b64encode(test_image).decode("ascii")

# Test different formats
formats = {
    "Format 1 - TGI style": {
        "inputs": "What is in this image?",
        "parameters": {"max_new_tokens": 100, "image": encoded},
    },
    "Format 2 - Direct inputs": {
        "inputs": {"prompt": "What is in this image?", "image": encoded}
    },
    "Format 3 - Text + image fields": {
        "text": "What is in this image?",
        "image": encoded,
    },
    "Format 4 - Inputs string with parameters": {
        "inputs": "What is in this image?",
        "parameters": {"image": encoded, "max_new_tokens": 100},
    },
}

for name, payload in formats.items():
    print(f"\nTesting {name}...")
    print(f"Payload keys: {list(payload.keys())}")
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                print("SUCCESS! Response:")
                print(json.dumps(data, indent=2)[:500])
                break
            except Exception:
                print(f"Response text: {response.text[:200]}")
        else:
            print(f"Error: {response.text[:200]}")
    except Exception as e:
        print(f"ERROR: {e}")
