#!/usr/bin/env python3
"""Test vLLM format with HuggingFace endpoint."""
import sys
import base64
import httpx
from pathlib import Path

sys.path.insert(0, "src")
from app.core.config import settings


def test_vllm_format():
    """Test the vLLM/OpenAI-compatible format."""
    # Find a test image
    test_image = list(Path("data/med-mmhl").rglob("*.jpg"))[0]
    print(f"Testing with image: {test_image}")

    with open(test_image, "rb") as f:
        image_bytes = f.read()

    # Detect image format
    image_format = "jpeg"
    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    image_url = f"data:image/{image_format};base64,{encoded_image}"

    # OpenAI-compatible chat completions format
    content = [
        {
            "type": "text",
            "text": """Return ONLY valid JSON:
{
  "veracity": "true",
  "alignment": "aligns_fully",
  "veracity_reasoning": "test",
  "alignment_reasoning": "test"
}""",
        },
        {"type": "image_url", "image_url": {"url": image_url}},
    ]

    payload = {
        "model": settings.medgemma_hf_model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 500,
    }

    # Try multiple URL formats
    base_url = settings.medgemma_vllm_url.rstrip("/")
    candidate_urls = [
        f"{base_url}/v1/chat/completions",
        f"{base_url}/chat/completions",
    ]

    headers = {}
    if settings.medgemma_hf_token:
        headers["Authorization"] = f"Bearer {settings.medgemma_hf_token}"

    for url in candidate_urls:
        print(f"\nTrying URL: {url}")
        try:
            with httpx.Client(timeout=90.0) as client:
                response = client.post(url, headers=headers, json=payload)
                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success!")
                    print(f"Response type: {type(data)}")
                    if isinstance(data, dict):
                        print(f"Keys: {list(data.keys())}")
                        if "choices" in data:
                            print(f"Choices: {len(data['choices'])}")
                            if data["choices"]:
                                msg = data["choices"][0].get("message", {})
                                content = msg.get("content", "")
                                print(f"\nContent (first 500 chars):\n{content[:500]}")
                    return
                elif response.status_code == 404:
                    print(f"❌ 404 Not Found - trying next URL...")
                    continue
                else:
                    print(f"❌ Error {response.status_code}")
                    print(f"Response: {response.text[:500]}")

        except httpx.ReadTimeout:
            print(f"❌ Timeout after 90 seconds")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_vllm_format()
