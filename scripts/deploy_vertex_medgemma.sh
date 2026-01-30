#!/usr/bin/env bash
set -euo pipefail

# Optional: upgrade SDK
uv run pip install --upgrade google-cloud-aiplatform

# Optional: login for ADC (interactive) if needed
if ! gcloud auth application-default print-access-token >/dev/null 2>&1; then
  gcloud auth application-default login
fi

PROJECT_ID="${PROJECT_ID:-medcontext}"
LOCATION="${LOCATION:-us-central1}"
MODEL_ID="${MODEL_ID:-google/medgemma@medgemma-1.5-4b-it}"
MACHINE_TYPE="${MACHINE_TYPE:-g2-standard-24}"
ACCELERATOR_TYPE="${ACCELERATOR_TYPE:-NVIDIA_L4}"
ACCELERATOR_COUNT="${ACCELERATOR_COUNT:-2}"
ENDPOINT_DISPLAY_NAME="${ENDPOINT_DISPLAY_NAME:-google_medgemma-1_5-4b-it-mg-one-click-deploy}"
MODEL_DISPLAY_NAME="${MODEL_DISPLAY_NAME:-google_medgemma-1_5-4b-it-$(date +%s)}"

python - <<PY
import vertexai
from vertexai import model_garden

vertexai.init(project="${PROJECT_ID}", location="${LOCATION}")

model = model_garden.OpenModel("${MODEL_ID}")
endpoint = model.deploy(
    accept_eula=True,
    machine_type="${MACHINE_TYPE}",
    accelerator_type="${ACCELERATOR_TYPE}",
    accelerator_count=int("${ACCELERATOR_COUNT}"),
    endpoint_display_name="${ENDPOINT_DISPLAY_NAME}",
    model_display_name="${MODEL_DISPLAY_NAME}",
    use_dedicated_endpoint=True,
)
print("Endpoint:", endpoint.resource_name)
PY
