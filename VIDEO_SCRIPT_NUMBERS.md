# Video Script - Correct Numbers Reference

## ✅ Use These Numbers (All Files Now Consistent)

### Med-MMHL Validation Dataset
- **Total samples**: 1,785 (full Med-MMHL test set)
- **Evaluated sample**: n=163 (stratified random, seed=42)
- **Misinformation rate**: 83.4% (136/163 misinformation, 27 legitimate)
- **Sources**: LeadStories, FactCheck.org, Snopes, Health Authorities

### Individual Signal Performance
- **Veracity only**: 79.8% accuracy
- **Alignment only**: 86.5% accuracy
- **Simple combination (naive)**: ~83% accuracy (plateaus)

### Optimized System Performance (MedGemma 4B Q4_KM Quantized)
- **Accuracy**: 92.0% [87.7%, 95.7%] (95% bootstrap CI)
- **Precision**: 96.2% (96 out of 100 flags are correct)
- **Recall**: 94.1% (catches 94 out of 100 misinformation cases)
- **F1 Score**: 95.1% (balanced performance)

### Confusion Matrix
- **True Positives (TP)**: 128 (misinformation correctly flagged)
- **False Positives (FP)**: 5 (legitimate incorrectly flagged)
- **True Negatives (TN)**: 22 (legitimate correctly identified)
- **False Negatives (FN)**: 8 (misinformation missed)

### Optimization Details
- **Decision logic**: VERACITY_FIRST
- **Thresholds**: 0.65 (veracity), 0.30 (alignment)
- **Method**: 5-fold cross-validation with bootstrap CIs
- **Model**: MedGemma 4B Q4_KM (4-bit quantized via llama-cpp-python)

### Performance Gains
- **From veracity alone**: +12.2 percentage points (79.8% → 92.0%)
- **From alignment alone**: +5.5 percentage points (86.5% → 92.0%)
- **From simple combination**: +9 percentage points (~83% → 92.0%)

---

## 🎯 Key Message Points

### The Problem
"The majority of medical misinformation uses **authentic images** with **misleading claims**—not fake images."

### The Gap
"Individual signals are insufficient:
- Veracity alone: 79.8%
- Alignment alone: 86.5%
- Simple combination: plateaus around 83%"

### The Breakthrough
"Hierarchical optimization with smart thresholds (0.65/0.30) and VERACITY_FIRST logic achieves **92% accuracy**—a breakthrough over individual signals."

### The Validation
"Validated on Med-MMHL: 163 stratified random samples from 1,785 fact-checked cases. Bootstrap 95% confidence: [87.7%, 95.7%]."

### The Impact
"Partnership with HERO Lab, UBC for deployment to African Ministries of Health. Target: millions of patients via Telegram bot integration."

---

## ❌ DO NOT Use These Old Numbers

- ~~65-72% single methods~~ → Use **79.8%/86.5%**
- ~~96.3% combined~~ → Use **92.0%**
- ~~71% veracity~~ → Use **79.8%**
- ~~78% alignment~~ → Use **86.5%**
- ~~91% optimized~~ → Use **92.0%**

---

## 📊 One-Sentence Summary

"MedContext transforms weak individual signals (veracity 79.8%, alignment 86.5%) into a 92% accurate misinformation detector through hierarchical optimization with smart thresholds—validated on 163 Med-MMHL fact-checked samples."

---

**Date**: February 22, 2026
**Model**: MedGemma 4B Q4_KM Quantized
**Dataset**: Med-MMHL (n=163, stratified random, seed=42)
