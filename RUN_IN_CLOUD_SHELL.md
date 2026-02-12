# Running Validation in Google Cloud Shell

The easiest way to run validation with the Vertex AI dedicated endpoint is to use Cloud Shell, where DNS resolution works automatically.

## Quick Start

1. **Open Cloud Shell** in your GCP project:
   ```bash
   # Go to: https://console.cloud.google.com/home/dashboard?project=1050549225427
   # Click the Cloud Shell icon (>_) in the top right
   ```

2. **Clone and setup the repo**:
   ```bash
   git clone <your-repo-url> medcontext
   cd medcontext
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

3. **Set environment variables**:
   ```bash
   export MEDGEMMA_PROVIDER=vertex
   export MEDGEMMA_VERTEX_PROJECT=1050549225427
   export MEDGEMMA_VERTEX_LOCATION=us-central1
   export MEDGEMMA_VERTEX_ENDPOINT=mg-endpoint-808a76f3-7b2b-49c0-b005-25ef07ed1926
   export MEDGEMMA_VERTEX_DEDICATED_DOMAIN=3407605337291751424.us-central1-1050549225427.prediction.vertexai.goog
   ```

4. **Authenticate** (Cloud Shell uses your user credentials automatically):
   ```bash
   gcloud auth application-default login
   ```

5. **Download Med-MMHL data** (if not already present):
   ```bash
   python scripts/download_med_mmhl.py --output data/med-mmhl
   ```

6. **Run validation on n=20**:
   ```bash
   python scripts/validate_med_mmhl.py \
     --data-dir data/med-mmhl \
     --split test \
     --limit 20 \
     --output validation_results/med_mmhl_n20
   ```

## Advantages of Cloud Shell

- ✅ DNS resolution works automatically (no IP address needed)
- ✅ ADC (Application Default Credentials) already configured
- ✅ Inside GCP VPC with access to dedicated endpoints
- ✅ No local environment setup needed
- ✅ Free to use (5GB persistent home directory)

## Alternative: Cloud Compute VM

If you need more resources:

```bash
# Create a VM in the same VPC
gcloud compute instances create medcontext-validator \
  --project=1050549225427 \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --scopes=cloud-platform

# SSH into it
gcloud compute ssh medcontext-validator --project=1050549225427 --zone=us-central1-a

# Then follow the same setup steps as Cloud Shell
```
