#!/usr/bin/env python3
"""
Script to check and undeploy Vertex AI endpoint
"""

import argparse
import os
import sys

import vertexai
from google.cloud import aiplatform


def get_config():
    """Get configuration from CLI arguments or environment variables."""
    parser = argparse.ArgumentParser(
        description="Check and undeploy Vertex AI endpoint"
    )
    parser.add_argument("--project-id", help="Google Cloud Project ID")
    parser.add_argument("--location", help="Google Cloud Location")
    parser.add_argument("--endpoint-id", help="Vertex AI Endpoint ID")

    args = parser.parse_args()

    # Try to get values from CLI arguments first, then from environment variables
    project_id = args.project_id or os.environ.get("PROJECT_ID")
    location = args.location or os.environ.get("LOCATION", "us-central1")
    endpoint_id = args.endpoint_id or os.environ.get("ENDPOINT_ID")

    # Validate that required values are present
    if not project_id:
        print(
            "Error: Project ID is required. Supply via --project-id argument or PROJECT_ID environment variable."
        )
        sys.exit(1)

    if not endpoint_id:
        print(
            "Error: Endpoint ID is required. Supply via --endpoint-id argument or ENDPOINT_ID environment variable."
        )
        sys.exit(1)

    return project_id, location, endpoint_id


def main():
    PROJECT_ID, LOCATION, ENDPOINT_ID = get_config()

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

        print("\nTarget endpoint found!")
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

        # Ask for confirmation to undeploy
        response = input("\nDo you want to undeploy this endpoint? (y/N): ")
        if response.lower() == "y":
            print("Undeploying all models from endpoint...")
            try:
                # Call endpoint.undeploy_all() inside new try/except to handle failures
                # and report without falling through to the outer handler that lists endpoints
                endpoint.undeploy_all()
                print(
                    "Undeployment initiated. Models will be removed from the endpoint."
                )
            except Exception as e:
                print(f"Error during undeployment: {e}")
                print(
                    "Undeployment failed. Please check the error details above and retry if needed."
                )
                return  # Exit to avoid executing the outer error path
        else:
            print("Undeployment cancelled.")

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
