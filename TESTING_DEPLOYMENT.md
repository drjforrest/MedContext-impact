# Testing Provider Configuration on VPS

## Step 1: Update Backend Code on VPS

```bash
# On your local machine - push changes to git
git add -A
git commit -m "feat: add configurable provider support with UI"
git push origin main

# SSH into VPS
ssh admin@vmi3089488

# Navigate to project
cd /var/www/medcontext/medcontext

# Pull latest changes
git pull origin main

# Restart the backend
pkill -f uvicorn
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir src &

# Verify it's running
sleep 3
curl http://localhost:8000/health
```

## Step 2: Build and Deploy Frontend

```bash
# Still on VPS, navigate to UI directory
cd /var/www/medcontext/medcontext/ui

# Install dependencies (if needed)
npm install

# Build the frontend
npm run build

# Copy build to web root (adjust path based on your web server config)
# If using Caddy:
sudo cp -r dist/* /var/www/medcontext/dist/

# If using Nginx:
# sudo cp -r dist/* /var/www/html/
```

## Step 3: Test Backend API

```bash
# Test provider endpoint
curl http://localhost:8000/api/v1/orchestrator/providers | python3 -m json.tool

# Expected output:
# [
#   {
#     "id": "medgemma-4b-quantized",
#     "provider": "llama_cpp",
#     "available": true,
#     "model": "llama_cpp/medgemma-1.5-4b-it-Q4_K_M"
#   }
# ]

# Test modules endpoint
curl http://localhost:8000/api/v1/modules | python3 -m json.tool
```

## Step 4: Test Frontend

Open in browser: `https://medcontext.drjforrest.com` (or your domain)

### Test Checklist:

#### Main Interface
- [ ] Status badge shows "🖥️ Local GGUF (Free)"
- [ ] Badge is green/success color
- [ ] "Configure" button is visible
- [ ] Clicking "Configure" navigates to Settings tab

#### Settings & Tools Tab
- [ ] New "Provider Configuration" tab is visible (should be first)
- [ ] Benefits comparison panel shows 3 options
- [ ] Current status shows: "Current Provider: MedGemma 4B Quantized"
- [ ] Status shows "● Available" in green

#### Provider Configuration
- [ ] Local GGUF radio is selected by default
- [ ] Shows: "✅ Already configured on the server"
- [ ] HuggingFace option shows token input when selected
- [ ] Vertex AI option shows project/endpoint/key inputs when selected

#### LLM Configuration
- [ ] Gemini radio button visible
- [ ] OpenRouter radio button visible
- [ ] Shows API key input based on selection

#### Actions
- [ ] "Save Configuration" button works (saves to localStorage)
- [ ] "Test Connection" button calls API
- [ ] Shows success/error message after testing

## Step 5: Test Provider Switch (Optional)

If you want to test switching providers:

```bash
# On VPS, edit .env
nano /var/www/medcontext/medcontext/.env

# Change to HuggingFace (example):
# MEDGEMMA_PROVIDER=huggingface
# MEDGEMMA_HF_TOKEN=your_token_here

# Restart backend
pkill -f uvicorn
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir src &

# Test
curl http://localhost:8000/api/v1/orchestrator/providers | python3 -m json.tool

# Should now show huggingface provider
```

## Troubleshooting

### Frontend not updating
```bash
# Clear browser cache
# Or use incognito mode

# Check build was successful
ls -la /var/www/medcontext/dist/

# Check web server is serving correct directory
sudo systemctl status caddy  # or nginx
```

### Backend not responding
```bash
# Check if uvicorn is running
ps aux | grep uvicorn

# Check logs
tail -f /var/www/medcontext/medcontext/logs/*.log

# Test directly
curl http://localhost:8000/health
```

### Provider shows unavailable
```bash
# Check .env configuration
grep MEDGEMMA /var/www/medcontext/medcontext/.env

# Check model files exist
ls -lh /var/www/medcontext/models/*.gguf

# Check llama-cpp-python
.venv/bin/python -c "import llama_cpp; print('OK')"
```

## Expected Results

✅ Main interface shows status badge
✅ Settings tab has new Provider Configuration section
✅ Current provider (Local GGUF) shows as available
✅ Save/Test buttons work
✅ Configuration persists in browser localStorage
✅ Users can see all provider options clearly

---

Ready to start? Let me know if you hit any issues!
