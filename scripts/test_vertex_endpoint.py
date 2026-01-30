#!/usr/bin/env python3
"""Test Vertex AI endpoint with a single prediction."""

import base64
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.core.config import settings

# Simple 1x1 red PNG
SAMPLE_IMAGE = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
    b"\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_with_sdk():
    """Test using google-cloud-aiplatform SDK."""
    print("Testing Vertex endpoint with SDK...")
    print(f"Project: {settings.medgemma_vertex_project}")
    print(f"Location: {settings.medgemma_vertex_location}")
    print(f"Endpoint: {settings.medgemma_vertex_endpoint}")

    try:
        from google.cloud import aiplatform
    except ImportError:
        print("❌ google-cloud-aiplatform not installed")
        return

    aiplatform.init(
        project=settings.medgemma_vertex_project,
        location=settings.medgemma_vertex_location,
    )

    endpoint = aiplatform.Endpoint(settings.medgemma_vertex_endpoint)
    encoded = base64.b64encode(SAMPLE_IMAGE).decode("ascii")

    # Use chat completions format for vLLM
    instance = {
        "@requestFormat": "chatCompletions",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{encoded}"},
                    },
                ],
            }
        ],
        "max_tokens": 200,
    }

    try:
        prediction = endpoint.predict(instances=[instance])
        print("✅ SDK prediction succeeded")
        print(f"Response: {prediction.predictions}")
    except Exception as exc:
        print(f"❌ SDK prediction failed: {exc}")


def test_with_rest():
    """Test using REST API with API key."""
    if not settings.vertexai_api_key:
        print("⚠️  VERTEXAI_API_KEY not set; skipping REST test")
        return

    print("\nTesting Vertex endpoint with REST API...")

    import httpx

    # Try to get dedicated domain from first SDK call
    try:
        from google.cloud import aiplatform

        aiplatform.init(
            project=settings.medgemma_vertex_project,
            location=settings.medgemma_vertex_location,
        )
        endpoint_obj = aiplatform.Endpoint(settings.medgemma_vertex_endpoint)
        # Extract numeric ID from resource name
        endpoint_id = settings.medgemma_vertex_endpoint.split("/")[-1]
        # Check if it has dedicated domain info
        if hasattr(endpoint_obj, "network"):
            print(f"Endpoint network: {endpoint_obj.network}")
    except Exception:
        pass

    resource = settings.medgemma_vertex_endpoint

    # Use dedicated domain if set, otherwise shared domain
    if settings.medgemma_vertex_dedicated_domain:
        domain = settings.medgemma_vertex_dedicated_domain.rstrip("/")
        url = f"https://{domain}/v1/{resource}:predict"
    else:
        url = (
            f"https://{settings.medgemma_vertex_location}-aiplatform.googleapis.com/v1/"
            f"{resource}:predict"
        )
    print(f"URL: {url}")

    encoded = base64.b64encode(SAMPLE_IMAGE).decode("ascii")

    # Use chat completions format for vLLM
    instance = {
        "@requestFormat": "chatCompletions",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{encoded}"},
                    },
                ],
            }
        ],
        "max_tokens": 200,
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                url,
                params={"key": settings.vertexai_api_key},
                json={"instances": [instance]},
            )
            response.raise_for_status()
            print("✅ REST prediction succeeded")
            print(f"Response: {response.json()}")
    except httpx.HTTPError as exc:
        print(f"❌ REST prediction failed: {exc}")
        if hasattr(exc, "response") and exc.response:
            print(f"Status: {exc.response.status_code}")
            print(f"Body: {exc.response.text[:500]}")


if __name__ == "__main__":
    test_with_sdk()
    test_with_rest()
