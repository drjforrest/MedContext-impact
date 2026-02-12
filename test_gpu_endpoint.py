#!/usr/bin/env python3
"""Quick test of GPU endpoint."""
import sys
from pathlib import Path

sys.path.insert(0, "src")
from app.clinical.medgemma_client import MedGemmaClient

# Find test image
test_image = list(Path("data/med-mmhl").rglob("*.jpg"))[0]
print(f"Testing GPU endpoint with: {test_image}\n")

# Read image
with open(test_image, "rb") as f:
    image_bytes = f.read()

# Simple test prompt
prompt = """Return ONLY valid JSON:
{
  "veracity": "true|partially_true|false",
  "alignment": "aligns_fully|partially_aligns|does_not_align",
  "veracity_reasoning": "brief explanation",
  "alignment_reasoning": "brief explanation"
}

Analyze this medical image."""

client = MedGemmaClient()
print(f"Provider: {client.provider}")

try:
    print("Sending request to GPU endpoint...")
    import time

    start = time.time()

    result = client.analyze_image(image_bytes=image_bytes, prompt=prompt)

    elapsed = time.time() - start
    print(f"✅ Success! Response time: {elapsed:.1f}s\n")
    print(f"Provider: {result.provider}")
    print(f"Model: {result.model}")
    print(f"\nParsed output:")
    import json

    print(json.dumps(result.output, indent=2))

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
