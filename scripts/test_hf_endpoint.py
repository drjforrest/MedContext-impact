#!/usr/bin/env python3
"""Test HuggingFace dedicated endpoint connection."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.clinical.medgemma_client import MedGemmaClient

def test_endpoint():
    """Test the MedGemma endpoint with a simple image."""
    client = MedGemmaClient()
    
    print(f"Provider: {client.provider}")
    print(f"Testing endpoint...")
    
    # Create a simple test image (1x1 red pixel PNG)
    test_image = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01\x00\x00\x00\x18\xdd\x8d\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    
    try:
        result = client.analyze_image(
            image_bytes=test_image,
            prompt="Describe this image briefly."
        )
        print(f"✅ Connection successful!")
        print(f"Provider: {result.provider}")
        print(f"Model: {result.model}")
        print(f"Raw response (first 200 chars): {result.raw_text[:200] if result.raw_text else 'None'}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_endpoint()
    sys.exit(0 if success else 1)
