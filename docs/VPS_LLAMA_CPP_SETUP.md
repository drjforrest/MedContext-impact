# VPS llama-cpp Setup Guide

## Pre-Deployment Verification

Before deploying to VPS with llama-cpp local inference, ensure the VPS is properly configured.

### Step 1: Verify VPS Configuration

Run the verification script from your **local machine**:

```bash
./scripts/verify_vps_llama_cpp.sh
```

This checks:
- ✅ Virtual environment exists
- ✅ llama-cpp-python is installed
- ✅ GGUF model files are present (`.gguf` and `mmproj`)
- ✅ .env file is configured correctly
- ✅ System resources are sufficient (RAM, disk)

### Step 2: Fix Any Issues

If verification fails, follow the instructions below:

## Common Setup Tasks

### 1. Install llama-cpp-python on VPS

If llama-cpp-python is not installed:

```bash
ssh Contabo-admin
cd /var/www/medcontext/medcontext
uv pip install llama-cpp-python
```

### 2. Download GGUF Models

If model files are missing:

```bash
ssh Contabo-admin
cd /var/www/medcontext/medcontext
./scripts/setup_llama_cpp.sh
```

This downloads:
- `medgemma-1.5-4b-it-Q4_K_M.gguf` (~2.4GB)
- `mmproj-F16.gguf` (~600MB)

Total: ~3GB download, 3GB disk space

### 3. Configure .env File

Ensure your **local** `.env` file has llama-cpp configuration:

```bash
# MedGemma: llama-cpp local inference
MEDGEMMA_MODEL=llama_cpp/medgemma-1.5-4b-it-Q4_K_M
MEDGEMMA_LOCAL_PATH=models/medgemma-1.5-4b-it-Q4_K_M.gguf
MEDGEMMA_MMPROJ_PATH=models/mmproj-F16.gguf

# LLM Orchestrator (optional but recommended)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
LLM_ORCHESTRATOR=gemini-2.5-pro
LLM_WORKER=gemini-2.5-flash

# Database
DATABASE_URL=postgresql://medcontext:password@localhost:5432/medcontext

# Add-on modules (optional)
ENABLE_REVERSE_SEARCH=false
ENABLE_PROVENANCE=false
ENABLE_FORENSICS=false
```

Then sync it to VPS:

```bash
# Option 1: Manual upload
scp .env Contabo-admin:/var/www/medcontext/medcontext/

# Option 2: Let deploy_simple.sh handle it
# (it will sync the .env file automatically)
```

### 4. System Requirements

**Minimum:**
- RAM: 8GB (4GB available for the model)
- Disk: 5GB free (3GB for models + overhead)
- CPU: 4+ cores recommended

**Recommended:**
- RAM: 16GB
- Disk: 10GB free
- CPU: 8+ cores

**Performance:**
- Q4_K_M quantization: ~2-3 tokens/sec on 4-core CPU
- First request: ~10-15 seconds (model loading)
- Subsequent requests: ~5-10 seconds (image analysis)

## Deployment Workflow

### Full Deployment with Verification

```bash
# 1. Verify configuration
./scripts/verify_vps_llama_cpp.sh

# 2. If verification passes, deploy
./scripts/deploy_simple.sh

# 3. Test deployment
curl https://medcontext.drjforrest.com/health
curl https://medcontext.drjforrest.com/api/v1/orchestrator/providers
```

### Quick Deploy (Skip Verification)

If you're confident everything is set up:

```bash
./scripts/deploy_simple.sh
```

## Troubleshooting

### Issue: llama-cpp-python Import Error

```bash
ssh Contabo-admin
cd /var/www/medcontext/medcontext
uv pip uninstall llama-cpp-python
uv pip install llama-cpp-python --force-reinstall
```

### Issue: Model Files Not Found

Check paths in .env match actual file locations:

```bash
ssh Contabo-admin
cd /var/www/medcontext/medcontext
ls -lh models/*.gguf
cat .env | grep MEDGEMMA
```

### Issue: Out of Memory

The Q4_K_M model needs ~4GB RAM. If running out of memory:

```bash
# Check current usage
free -h

# Stop other services to free RAM
sudo systemctl stop other-service

# Or use smaller Q2_K quantization (download separately)
```

### Issue: Model Loading Timeout

First request takes 10-15 seconds to load model. This is normal.

If it times out:
1. Check backend logs: `journalctl -u medcontext -n 50`
2. Increase uvicorn timeout in systemd service
3. Consider using Q2_K quantization (loads faster)

### Issue: Backend Won't Start

Check logs:

```bash
ssh Contabo-admin
journalctl -u medcontext -n 100 -f
```

Common causes:
- Missing .env file
- Invalid paths in .env
- llama-cpp-python not installed
- Model files not downloaded

## Performance Optimization

### 1. Use Q4_K_M (Default)

Best balance of quality and speed:
- Size: 2.4GB
- Speed: ~2-3 tokens/sec
- Quality: Excellent

### 2. Use Q2_K (Faster)

For faster inference at cost of some quality:
- Size: 1.6GB
- Speed: ~4-5 tokens/sec
- Quality: Good

Download Q2_K:
```bash
ssh Contabo-admin
cd /var/www/medcontext/medcontext
# Download Q2_K version (update download script)
```

### 3. GPU Acceleration (Advanced)

If VPS has GPU:

```bash
# Install CUDA version of llama-cpp-python
uv pip uninstall llama-cpp-python
CMAKE_ARGS="-DLLAMA_CUBLAS=on" uv pip install llama-cpp-python
```

This can give 10-50x speedup depending on GPU.

## Monitoring

### Check Model Status

```bash
curl https://medcontext.drjforrest.com/api/v1/orchestrator/providers | jq
```

Should show:
```json
{
  "llama_cpp": {
    "status": "healthy",
    "model": "medgemma-1.5-4b-it-Q4_K_M.gguf",
    "provider": "llama_cpp"
  }
}
```

### Check Resource Usage

```bash
ssh Contabo-admin

# RAM usage
free -h

# CPU usage
top -bn1 | grep medcontext

# Disk usage
df -h /var/www/medcontext
```

### Check Logs

```bash
# Real-time logs
ssh Contabo-admin 'journalctl -u medcontext -f'

# Recent errors
ssh Contabo-admin 'journalctl -u medcontext -n 100 | grep ERROR'
```

## Quick Reference

```bash
# Verify before deploy
./scripts/verify_vps_llama_cpp.sh

# Deploy
./scripts/deploy_simple.sh

# Check logs
ssh Contabo-admin 'journalctl -u medcontext -f'

# Restart service
ssh Contabo-admin 'sudo systemctl restart medcontext'

# Test health
curl https://medcontext.drjforrest.com/health
```
