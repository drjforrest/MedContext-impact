# 👋 Welcome Judges! Start Here

**Thank you for reviewing MedContext!**

This guide will help you quickly understand our submission and navigate the documentation efficiently.

---

## ⏱️ Quick Navigation by Time Available

### Have 2 minutes?

📄 **Read:** [docs/EXECUTIVE_SUMMARY.md](docs/EXECUTIVE_SUMMARY.md)

One-page overview covering:

- The problem (over half of misinformation uses authentic images with misleading context)
- Our validation (DICOM-native pixel forensics: 97.5% for tampering; contextual analysis: 65.6% for image-claim alignment)
- The solution (agentic contextual authenticity combining both approaches)

### Have 15 minutes?

**Recommended Reading Path:**

1. [EXECUTIVE_SUMMARY.md](docs/EXECUTIVE_SUMMARY.md) - The pitch
2. [VALIDATION.md](docs/VALIDATION.md) - Our empirical evidence
3. [SUBMISSION.md](docs/SUBMISSION.md) - Comprehensive submission
4. [Demo Video](#-demo-video) - See it in action (3 min)

### Want to verify our claims?

**Run the system yourself** (5 minutes):

**🐳 Option 1: Docker (Easiest - Recommended)**

```bash
# 1. Configure
cp .env.example .env
# Add: MEDGEMMA_HF_TOKEN=hf_your_token

# 2. Launch everything
docker-compose up -d

# Visit http://localhost for UI
# Visit http://localhost:8000/docs for API
```

**🛠️ Option 2: Manual Setup**

```bash
# 1. Install
uv venv && uv run pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Add: MEDGEMMA_HF_TOKEN=hf_your_token

# 3. Run tests
uv run pytest tests/ -v
# Expected: 45/45 passed

# 4. Start system
uv run uvicorn app.main:app --reload --app-dir src
# Visit http://localhost:8000/docs for API
```

See **[DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)** for complete Docker guide.

---

## 🎯 What Makes MedContext Different

### Most projects would optimize for:

- ❌ Synthetic benchmark datasets
- ❌ Deepfake detection (sophisticated manipulations)
- ❌ Pixel-level forensics

### MedContext optimizes for:

- ✅ **Real-world threat distribution** (majority authentic images with false context)
- ✅ **Empirically validated** (proved pixel forensics cannot detect image-claim misalignment; contextual analysis achieves 65.6% accuracy)
- ✅ **Production deployment** (UBC HERO Lab partnership ready)

---

## 📊 Key Evidence

**Our Validation Proves the Dual-Layer Approach:**

**Validation Results:**

| Layer                   | Signal                           | Performance                                       | Dataset              |
| ----------------------- | -------------------------------- | ------------------------------------------------- | -------------------- |
| **Pixel Forensics**     | DICOM-native tampering detection | **97.5% accuracy** (100% precision, 96.7% recall) | 160 medical images   |
| **Contextual Analysis** | Image-claim alignment            | **65.6% accuracy** [95% CI: 55.6%, 75.6%]         | 90 image-claim pairs |
| **Contextual Analysis** | Alignment signal (ROC AUC)       | **0.740** with 0.44 separation                    | 90 image-claim pairs |

**Why Both Layers Are Necessary:**

- **Pixel forensics** solves tampering detection (97.5% accuracy on image integrity)
- **Contextual analysis** addresses the dominant threat: authentic images with misleading claims (65.6% on alignment)
- Literature shows 80%+ of medical misinformation uses authentic images in false contexts (Brennen et al., 2021)

**Key Validation Insight:** Pixel-level tampering detection alone is insufficient. The real-world threat requires contextual authenticity verification.

[See full validation methodology → docs/VALIDATION.md]

---

## 🤖 Agentic Innovation

### 3-Step Autonomous Workflow

```
1. TRIAGE (MedGemma)
   ↓ Analyzes image → determines required tools

2. DYNAMIC DISPATCH
   ↓ Selectively invokes tools (60% faster for genuine images):
     • Reverse search if context matters
     • Forensics if suspicious
     • Provenance for verification

3. SYNTHESIS (LLM/MedGemma)
   ↓ Aggregates evidence → alignment verdict with rationale
```

**Not just "AI-powered"—truly autonomous decision-making.**

[See technical details → docs/AGENTIC_WORKFLOW.md]

---

## 📁 Documentation Map

```
medcontext/
├── START_HERE.md                  ← You are here
├── README.md                       ← Project overview
├── docs/
│   ├── EXECUTIVE_SUMMARY.md       ← 1-page pitch (START HERE)
│   ├── VALIDATION.md              ← Two validation studies (ELA 49.9% → DICOM 97.5%; contextual 65.6%)
│   ├── VALIDATION_RESULTS.md      ← Detailed metrics and analysis
│   ├── VALIDATION_DATASETS.md     ← Dataset specifications
│   ├── SUBMISSION.md              ← Comprehensive submission
│   ├── AGENTIC_WORKFLOW.md        ← Technical deep dive
│   └── COMPETITION_RULES.md       ← Competition requirements
├── src/                           ← Source code (4,100+ lines Python)
├── tests/                         ← 45 passing tests
└── ui/                            ← React frontend
```

---

## ✅ Verification Checklist

- [ ] **Innovation?** ✅ Agentic system for contextual authenticity
- [ ] **Works?** ✅ 45/45 tests passing, full-stack implementation
- [ ] **Evidence?** ✅ Empirical validation with confidence intervals
- [ ] **Impact?** ✅ HERO Lab partnership for African deployment
- [ ] **Documentation?** ✅ 5 comprehensive documents, white paper
- [ ] **Reproducible?** ✅ Setup in 5 minutes, HuggingFace provider for judges

## 📹 Demo Video

[Video embed - currently in production]

**3-minute demonstration covering:**

1. The problem (authentic images used misleadingly)
2. Dual-layer validation (97.5% tampering detection + 65.6% alignment verification)
3. Live demo (upload → analysis → verdict)
4. Impact (HERO Lab partnership for Africa)

> Note: Competition requirement is 3 minutes maximum

---

## 💬 Contact

**Developer:** Jamie Forrest
**Email:** forrest.jamie@gmail.com | james.forrest@ubc.ca
**Affiliation:** Scientific Director, HERO Lab, School of Nursing, University of British Columbia

**Questions?**

- Setup issues: See [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)
- Technical details: [docs/AGENTIC_WORKFLOW.md](docs/AGENTIC_WORKFLOW.md)
- Validation methodology: [docs/VALIDATION.md](docs/VALIDATION.md)
- API documentation: `http://localhost:8000/docs` (when running)

---

## 🚀 Next Steps for Judges

### Option 1: Quick Review (10 min)

1. Read [EXECUTIVE_SUMMARY.md](docs/EXECUTIVE_SUMMARY.md)
2. Read [VALIDATION.md - Part 1](docs/VALIDATION.md)
3. Watch demo video

### Option 2: Comprehensive Review (30 min)

1. Read [EXECUTIVE_SUMMARY.md](docs/EXECUTIVE_SUMMARY.md)
2. Read [VALIDATION.md](docs/VALIDATION.md)
3. Read [SUBMISSION.md](docs/SUBMISSION.md)
4. Watch demo video
5. Check [AGENTIC_WORKFLOW.md](docs/AGENTIC_WORKFLOW.md) for technical depth

### Option 3: Hands-On Verification (45 min)

1. Run setup commands above
2. Execute test suite (45 tests)
3. Start system and test API
4. Upload test image via UI
5. Review code architecture

---

**Thank you for reviewing MedContext!**

We're excited to show how agentic AI can address the real-world visual medical misinformation problem—not by chasing synthetic benchmarks, but by understanding context and meaning. This is evidence-based, production-ready, and ready for deployment. 🏥🤖
