#!/usr/bin/env python3
"""
Script to verify that the Vertex AI endpoint has been undeployed
"""

import sys

import vertexai
from google.api_core.exceptions import NotFound
from google.cloud import aiplatform

PROJECT_ID = "medcontext"
LOCATION = "us-central1"
ENDPOINT_ID = "mg-endpoint-51eed710-5889-4a87-a7e9-675990019775"


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
            sys.exit(1)  # Exit with non-zero status to indicate failure
        else:
            print("Endpoint has no deployed models.")
            sys.exit(1)  # Exit with non-zero status to indicate failure

    except NotFound as e:
        print(f"Endpoint not found: {e}")
        print("This indicates the endpoint has been successfully undeployed.")
        sys.exit(0)  # Exit with zero status to indicate success

    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        sys.exit(1)  # Exit with non-zero status to indicate failure


if __name__ == "__main__":
    main()
