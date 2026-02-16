#!/usr/bin/env python3
"""Test what the HF endpoint actually returns."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.clinical.medgemma_client import MedGemmaClient

# Create a simple test image (1x1 pixel PNG)
test_image = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "8900000010494441541863f8cfc0f0030000050002fef02cc0890000000049454e"
    "44ae426082"
)

prompt = """You are a medical image-context alignment analyzer. Return ONLY valid JSON:
{
  "veracity": "true|partially_true|false",
  "alignment": "aligns_fully|partially_aligns|does_not_align",
  "veracity_reasoning": "brief explanation",
  "alignment_reasoning": "brief explanation"
}

User Claim: "This shows a chest X-ray with pneumonia."""

client = MedGemmaClient()
print(f"Provider: {client.provider}")
print("\nCalling endpoint...")

try:
    result = client.analyze_image(image_bytes=test_image, prompt=prompt)
    print(f"\nProvider used: {result.provider}")
    print(f"Model: {result.model}")
    print("\nRaw text response:")
    print("=" * 60)
    print(result.raw_text if result.raw_text else "(no raw text)")
    print("=" * 60)
    print("\nParsed output:")
    print(result.output)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()
