#!/usr/bin/env python3
"""Test HuggingFace endpoint raw response."""
import sys
import base64
import httpx
from pathlib import Path

sys.path.insert(0, 'src')
from app.core.config import settings

def test_raw_endpoint():
    """Test the raw HuggingFace endpoint response."""
    # Find a test image
    test_image = list(Path("data/med-mmhl").rglob("*.jpg"))[0]
    print(f"Testing with image: {test_image}")

    with open(test_image, "rb") as f:
        image_bytes = f.read()

    encoded_image = base64.b64encode(image_bytes).decode("ascii")

    url = settings.medgemma_url.rstrip("/")
    headers = {"Authorization": f"Bearer {settings.medgemma_hf_token}"}

    prompt = """Return ONLY valid JSON:
{
  "veracity": "true",
  "alignment": "aligns_fully",
  "veracity_reasoning": "test",
  "alignment_reasoning": "test"
}"""

    # Test with TGI format (for dedicated endpoints)
    payload = {
        "inputs": prompt,
        "parameters": {
            "image": encoded_image,
            "max_new_tokens": 500,
        }
    }

    print(f"\nEndpoint URL: {url}")
    print(f"Payload keys: {list(payload.keys())}")
    print(f"Parameters keys: {list(payload['parameters'].keys())}")
    print(f"\nSending request...")

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            print(f"\nResponse status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"\nRaw response text (first 1000 chars):")
            print(response.text[:1000])

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"\nParsed JSON type: {type(data)}")
                    if isinstance(data, list):
                        print(f"List length: {len(data)}")
                        if data:
                            print(f"First item: {data[0]}")
                    elif isinstance(data, dict):
                        print(f"Dict keys: {list(data.keys())}")
                        print(f"Full dict: {data}")
                except Exception as e:
                    print(f"JSON parsing error: {e}")
            else:
                print(f"\n❌ Request failed with status {response.status_code}")
                print(f"Error: {response.text}")

    except Exception as e:
        print(f"\n❌ Request error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_raw_endpoint()
