#!/usr/bin/env python3
"""
Script to verify that the Vertex AI endpoint has been undeployed
"""

import vertexai
from google.cloud import aiplatform

PROJECT_ID = "medcontext"
LOCATION = "us-central1"
ENDPOINT_ID = "PLACEHOLDER_ENDPOINT_ID"


def main():
    print("Initializing Vertex AI...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    aiplatform.init(project=PROJECT_ID, location=LOCATION)

    # Get the endpoint name
    endpoint_name = (
        f"projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    )

    print(f"Checking if endpoint still exists: {endpoint_name}")

    try:
        # Try to get the endpoint
        endpoint = aiplatform.Endpoint(endpoint_name)
        print("Endpoint still exists!")
        print(f"Display name: {endpoint.display_name}")
        print(f"Resource name: {endpoint.resource_name}")

        # Check if it's still deployed
        deployed_models = endpoint.list_models()
        if deployed_models:
            print(
                "Endpoint still has deployed models. Undeployment may still be in progress."
            )
        else:
            print("Endpoint has no deployed models.")

    except Exception as e:
        print(f"Endpoint not found: {e}")
        print("This indicates the endpoint has been successfully undeployed.")


if __name__ == "__main__":
    main()
