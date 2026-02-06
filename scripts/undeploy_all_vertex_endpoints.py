#!/usr/bin/env python3
"""
Script to undeploy all Vertex AI endpoints for this project
"""

import vertexai
from google.cloud import aiplatform

PROJECT_ID = "medcontext"
LOCATION = "us-central1"


def main():
    print("Initializing Vertex AI...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    aiplatform.init(project=PROJECT_ID, location=LOCATION)

    print("Listing all endpoints in this project:")

    # List all endpoints
    endpoints_list = aiplatform.Endpoint.list()
    if not endpoints_list:
        print("No endpoints found in this project.")
        return

    print("Found endpoints:")
    for ep in endpoints_list:
        print(f"- {ep.display_name}: {ep.resource_name}")

    print("\nUndeploying all endpoints...")

    confirm = input(
        f"Are you sure you want to undeploy all {len(endpoints_list)} endpoint(s)? (yes/no): "
    )
    if confirm.lower() != "yes":
        print("Operation cancelled.")
        return

    for endpoint in endpoints_list:
        print(f"\nUndeploying endpoint: {endpoint.display_name}")
        print(f"Resource name: {endpoint.resource_name}")

        # Get deployed models
        deployed_models = endpoint.list_models()
        if deployed_models:
            print("Deployed models:")
            for model in deployed_models:
                print(f"- {model.model}")
        else:
            print("No deployed models found")

        try:
            endpoint.undeploy_all()
            print("Undeployment initiated.")
        except Exception as e:
            print(f"Error undeploying endpoint: {e}")

    print(
        "\nAll models have been undeployed from the endpoints. The endpoints themselves still exist."
    )


if __name__ == "__main__":
    main()
