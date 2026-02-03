#!/usr/bin/env python3
"""
Script to undeploy Vertex AI endpoint automatically
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

    # Get the endpoint
    endpoint_name = (
        f"projects/{PROJECT_ID}/locations/{LOCATION}/endpoints/{ENDPOINT_ID}"
    )

    print(f"Looking up endpoint: {endpoint_name}")

    try:
        # Get the endpoint
        endpoint = aiplatform.Endpoint(endpoint_name)

        print(f"\nTarget endpoint found!")
        print(f"Display name: {endpoint.display_name}")
        print(f"Resource name: {endpoint.resource_name}")

        # Get deployed models
        deployed_models = endpoint.list_models()
        if deployed_models:
            print("Deployed models:")
            for model in deployed_models:
                print(f"- {model.model}")
        else:
            print("No deployed models found")

        # Automatically undeploy the endpoint
        print("\nUndeploying endpoint...")
        endpoint.undeploy_all()
        print("Undeployment initiated. The endpoint will be deleted.")

    except Exception as e:
        print(f"Error accessing endpoint: {e}")
        print("\nListing all available endpoints in this project:")

        # List all endpoints
        endpoints_list = aiplatform.Endpoint.list()
        if endpoints_list:
            for ep in endpoints_list:
                print(f"- {ep.display_name}: {ep.resource_name}")
        else:
            print("No endpoints found in this project.")


if __name__ == "__main__":
    main()
