#!/usr/bin/env bash
set -euo pipefail

# Script to undeploy MedGemma model from Vertex AI

PROJECT_ID="${PROJECT_ID:-medcontext}"
LOCATION="${LOCATION:-us-central1}"
ENDPOINT_ID="${ENDPOINT_ID:-PLACEHOLDER_ENDPOINT_ID}"

# Optional: login for ADC (interactive) if needed
if ! gcloud auth application-default print-access-token >/dev/null 2>&1; then
  gcloud auth application-default login
fi

echo "Undeploying Vertex AI endpoint: ${ENDPOINT_ID}"
echo "Project: ${PROJECT_ID}"
echo "Location: ${LOCATION}"

python - <<PY
import vertexai
from vertexai import endpoints

vertexai.init(project="${PROJECT_ID}", location="${LOCATION}")

# Get the endpoint
endpoint_name = f"projects/${PROJECT_ID}/locations/${LOCATION}/endpoints/${ENDPOINT_ID}"

print(f"Looking up endpoint: {endpoint_name}")

# List all endpoints to verify the endpoint exists
all_endpoints = endpoints.Endpoint.list()
endpoint_found = False

for ep in all_endpoints:
    if ep.resource_name == endpoint_name:
        endpoint_found = True
        print(f"Found endpoint: {ep.display_name}")
        print(f"Endpoint state: {ep.state}")
        
        # Get deployed models
        if hasattr(ep, 'deployed_models') and ep.deployed_models:
            for model in ep.deployed_models:
                print(f"Deployed model: {model.model}")
        
        # Undeploy the endpoint
        print("Undeploying endpoint...")
        ep.undeploy_all()
        print("Undeployment initiated. Models removed from endpoint (endpoint resource still exists).")
        break

if not endpoint_found:
    print(f"Endpoint {endpoint_name} not found. It may have already been deleted.")
    
    # Try to list all endpoints to see what's available
    print("\nAvailable endpoints in this project:")
    for ep in all_endpoints:
        print(f"- {ep.display_name}: {ep.resource_name}")
PY

echo "Undeployment script completed."