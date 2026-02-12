#!/usr/bin/env python3
"""Test HuggingFace endpoint response."""
import sys
import json
from pathlib import Path

sys.path.insert(0, 'src')

from app.clinical.medgemma_client import MedGemmaClient

def test_endpoint():
    """Test the HuggingFace endpoint with a sample image."""
    client = MedGemmaClient()

    print(f"Provider: {client.provider}")

    # Find a test image from med-mmhl
    test_images = list(Path("data/med-mmhl").rglob("*.jpg"))[:1]

    if not test_images:
        print("No test images found")
        return

    test_image = test_images[0]
    print(f"\nTesting with image: {test_image}")

    # Read image
    with open(test_image, "rb") as f:
        image_bytes = f.read()

    # Simple prompt
    prompt = """You are a medical image analyzer. Return ONLY valid JSON:
{
  "veracity": "true|partially_true|false",
  "alignment": "aligns_fully|partially_aligns|does_not_align",
  "veracity_reasoning": "brief explanation",
  "alignment_reasoning": "brief explanation"
}

Analyze this medical image and the claim: "This shows COVID-19 test results"
"""

    try:
        print("\nSending request to HuggingFace endpoint...")
        result = client.analyze_image(image_bytes=image_bytes, prompt=prompt)

        print(f"\nResponse received:")
        print(f"  Provider: {result.provider}")
        print(f"  Model: {result.model}")
        print(f"\nRaw text response (first 500 chars):")
        print(result.raw_text[:500] if result.raw_text else "None")
        print(f"\nParsed output:")
        print(json.dumps(result.output, indent=2))

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_endpoint()
