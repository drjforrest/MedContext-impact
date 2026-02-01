# Contextual Signals Validation Framework

**Validating Medical Image Context Authenticity Detection**

---

## Executive Summary

This document outlines the empirical validation framework for MedContext's four contextual signals that detect medical image misinformation. Unlike pixel-level forensics (which achieved ~50% accuracy on manipulation detection), contextual signals target the 87% of medical misinformation cases where **authentic images are misused with misleading context**.

**Validation Objective:** Demonstrate that contextual signals can reliably detect when medical images are presented with false or misleading claims, even when the images themselves are authentic and unmanipulated.

---

## Table of Contents

1. [Contextual Signals Overview](#1-contextual-signals-overview)
2. [Validation Datasets](#2-validation-datasets)
3. [Evaluation Metrics](#3-evaluation-metrics)
4. [Signal-Specific Validation](#4-signal-specific-validation)
5. [Integrated Score Validation](#5-integrated-score-validation)
6. [Methodology](#6-methodology)
7. [Expected Baselines](#7-expected-baselines)
8. [Implementation Guide](#8-implementation-guide)
9. [Reproducibility](#9-reproducibility)

---

## 1. Contextual Signals Overview

MedContext computes a **Contextual Integrity Score** from four signals:

| Signal | Weight | Source | Range | Purpose |
|--------|--------|--------|-------|---------|
| **Alignment** | 60% | MedGemma/LLM synthesis | 0.0-1.0 | Does image content match claimed context? |
| **Plausibility** | 15% | MedGemma triage | 0.0-1.0 | Is the medical claim medically plausible? |
| **Genealogy Consistency** | 15% | Provenance tracking | 0.4-0.8 | Is the image usage history consistent? |
| **Source Reputation** | 10% | Reverse image search | 0.0-1.0 | Do credible sources use this image similarly? |

### Signal Definitions

#### 1.1 Alignment Signal
**Question:** Does the visual content of the image align with the textual claim?

**Example:**
- ✅ **Aligned:** Chest X-ray showing opacity + claim "pneumonia"
- ⚠️ **Partially Aligned:** CT brain scan + claim "stroke" (plausible but needs confirmation)
- ❌ **Misaligned:** Skin rash photo + claim "lung cancer"
- ❓ **Unclear:** Abstract medical diagram + vague claim

**Scoring:**
```python
alignment_labels = {
    "aligned": 1.0,
    "partially_aligned": 0.6,
    "misaligned": 0.0,
    "unclear": 0.3
}
# Final score = base_score * confidence
```

#### 1.2 Plausibility Signal
**Question:** Is the medical claim itself plausible based on visual evidence?

**Example:**
- **High (0.9):** Clear visual evidence supports claim
- **Medium (0.6):** Claim is possible but not definitively shown
- **Low (0.3):** Claim contradicts visual evidence or medical knowledge

#### 1.3 Source Reputation Signal
**Question:** Do authoritative sources use this image in similar contexts?

**Derived from:** Reverse image search confidence scores
- High confidence matches to medical journals → high reputation
- Matches to social media misinformation → low reputation
- No matches → neutral (0.5)

#### 1.4 Genealogy Consistency Signal
**Question:** Is the provenance chain intact and consistent?

**Binary assessment:**
- **0.8:** Provenance completed with valid hash chain
- **0.4:** Provenance missing or incomplete

---

## 2. Validation Datasets

### 2.1 Required Dataset Characteristics

For robust validation, we need datasets with:
1. **Authentic medical images** (not manipulated)
2. **Ground truth labels** for context alignment
3. **Diverse claim types:** Clinical diagnoses, treatment claims, health advice, news captions
4. **Known misinformation examples** from real-world cases

### 2.2 Proposed Datasets

#### Dataset A: Medical Image-Caption Pairs (Ground Truth)
**Source:** Curated from medical literature with verified captions
- **Size:** 500-1,000 image-claim pairs
- **Composition:**
  - 40% aligned (correct context)
  - 30% misaligned (wrong diagnosis/context)
  - 20% partially aligned (vague or incomplete)
  - 10% unclear (insufficient information)
- **Labels:** Expert-annotated by medical professionals
- **Example Sources:**
  - PubMed Central image database
  - Medical education repositories (MedPix, Radiopaedia)
  - Verified social media posts from health authorities

#### Dataset B: Social Media Misinformation Corpus
**Source:** Real misinformation cases from fact-checking organizations
- **Size:** 200-500 flagged posts
- **Composition:**
  - Authentic images with false captions
  - Images repurposed from unrelated contexts
  - Misleading treatment claims
- **Labels:** Fact-checker verdicts (true/false/misleading)
- **Example Sources:**
  - HealthFeedback.org verified claims
  - Snopes medical fact-checks
  - WHO infodemic reports

#### Dataset C: Synthetic Context Mismatches
**Source:** Programmatically generated mismatches
- **Size:** 300-500 pairs
- **Method:**
  - Take verified medical images with correct captions
  - Swap captions between unrelated images
  - Introduce factual errors (wrong anatomy, incorrect diagnoses)
- **Labels:** Automatically generated (known misalignments)

#### Dataset D: Temporal Provenance Cases
**Source:** Images with documented reuse history
- **Size:** 100-200 images
- **Composition:**
  - Images repurposed across multiple contexts
  - Images with known original sources
- **Labels:** Provenance chain verification
- **Example:** Stock medical image used in multiple unrelated news stories

### 2.3 Dataset Stratification

All datasets should be stratified by:
- **Modality:** X-ray, CT, MRI, ultrasound, dermoscopy, histology
- **Body Region:** Chest, brain, abdomen, skin, other
- **Claim Type:** Diagnosis, treatment, causation, prevention
- **Language:** English (primary), with multilingual subset if feasible

---

## 3. Evaluation Metrics

### 3.1 Signal-Level Metrics

For each individual signal:

#### Classification Metrics (with threshold = 0.5)
- **Accuracy:** Overall correctness
- **Precision:** Of positive predictions, how many are correct?
- **Recall:** Of actual positives, how many are detected?
- **F1 Score:** Harmonic mean of precision and recall
- **Matthews Correlation Coefficient (MCC):** Balanced measure for imbalanced datasets

#### Discrimination Metrics
- **ROC AUC:** Area under receiver operating characteristic curve
- **PR AUC:** Area under precision-recall curve (better for imbalanced data)
- **Calibration:** Do predicted probabilities match observed frequencies?

#### Distribution Analysis
- **Signal Separation:** Distance between aligned vs. misaligned distributions
- **Overlap:** Percentage of distribution overlap
- **Decision Threshold:** Optimal cutoff via Youden's J statistic

### 3.2 Integrated Score Metrics

For the combined Contextual Integrity Score:

#### Detection Performance
- **Accuracy @ 0.5 threshold:** Binary classification performance
- **Accuracy @ optimal threshold:** Performance at best threshold
- **Multi-class accuracy:** Aligned / Partially Aligned / Misaligned / Unclear

#### Confidence Calibration
- **Expected Calibration Error (ECE):** Difference between predicted confidence and accuracy
- **Reliability Diagram:** Visual calibration assessment

#### Ablation Analysis
- **Signal Contribution:** Performance with each signal removed
- **Weight Sensitivity:** Impact of weight adjustments
- **Failure Mode Analysis:** Which cases are systematically misclassified?

### 3.3 Statistical Rigor

All metrics reported with:
- **95% Confidence Intervals** via bootstrap resampling (1,000+ iterations)
- **Statistical Significance Testing** for comparisons (McNemar's test for classifiers)
- **Effect Sizes** (Cohen's d for distribution differences)

---

## 4. Signal-Specific Validation

### 4.1 Alignment Signal Validation

**Hypothesis:** MedGemma can distinguish between aligned and misaligned image-claim pairs.

#### Validation Protocol

1. **Dataset:** Use Dataset A (medical image-caption pairs) + Dataset B (misinformation corpus)
2. **Ground Truth:** Expert annotations (aligned / partially / misaligned / unclear)
3. **Procedure:**
   ```python
   for image, claim in dataset:
       result = medgemma_client.analyze_image(
           image_bytes=image,
           context=claim
       )
       predicted_alignment = extract_alignment_label(result)
       alignment_score = map_to_score(predicted_alignment, confidence)
       
       # Compare to ground truth
       record_prediction(predicted_alignment, ground_truth)
   ```

4. **Analysis:**
   - Confusion matrix: Predicted vs. actual alignment
   - ROC curve: Alignment score as continuous predictor
   - Error analysis: Which types of claims cause misclassifications?

#### Expected Performance Targets

| Metric | Minimum | Target | Stretch |
|--------|---------|--------|---------|
| Accuracy | 65% | 75% | 85% |
| ROC AUC | 0.70 | 0.80 | 0.90 |
| Precision (misaligned) | 70% | 80% | 90% |
| Recall (misaligned) | 60% | 70% | 80% |

**Rationale:** Medical context alignment is challenging due to ambiguous language and visual similarity between conditions. 75% accuracy would be meaningful.

#### Key Questions to Answer

1. Does MedGemma correctly identify obvious misalignments? (e.g., skin rash + lung cancer claim)
2. How does it handle ambiguous cases? (e.g., chest X-ray + vague respiratory claim)
3. Does it avoid false positives on correctly aligned pairs?
4. What role does claim specificity play? (specific diagnosis vs. vague symptom)

### 4.2 Plausibility Signal Validation

**Hypothesis:** MedGemma can assess medical plausibility of claims given visual evidence.

#### Validation Protocol

1. **Dataset:** Dataset A + Dataset C (synthetic mismatches)
2. **Ground Truth:** 
   - High plausibility: Clear visual evidence supports claim
   - Medium plausibility: Claim possible but not definitive
   - Low plausibility: Claim contradicts visual evidence
3. **Procedure:**
   ```python
   for image, claim in dataset:
       triage_result = medgemma_client.analyze_image(
           image_bytes=image,
           prompt=triage_prompt
       )
       plausibility = extract_plausibility(triage_result)
       plausibility_score = map_plausibility_to_score(plausibility)
       
       # Compare to ground truth
       record_prediction(plausibility_score, ground_truth)
   ```

4. **Analysis:**
   - Correlation between predicted and actual plausibility
   - Agreement with medical expert judgments (Fleiss' kappa)
   - Calibration: Do "high" predictions actually align with evidence?

#### Expected Performance Targets

| Metric | Minimum | Target | Stretch |
|--------|---------|--------|---------|
| 3-way accuracy | 55% | 65% | 75% |
| Spearman correlation | 0.50 | 0.65 | 0.80 |
| Low vs. High discrimination (AUC) | 0.75 | 0.85 | 0.93 |

**Rationale:** Medical plausibility is subjective and context-dependent. Even moderate performance is valuable.

### 4.3 Source Reputation Signal Validation

**Hypothesis:** Reverse image search can identify reputable vs. unreliable sources.

#### Validation Protocol

1. **Dataset:** Dataset B (social media misinformation) + Dataset D (provenance cases)
2. **Ground Truth:**
   - High reputation: Medical journals, hospitals, health authorities
   - Medium reputation: News media, educational sites
   - Low reputation: Social media, unverified blogs, known misinformation sites
3. **Procedure:**
   ```python
   for image in dataset:
       search_results = reverse_search_service.search(image)
       reputation_score = compute_source_reputation(search_results)
       
       # Compare to ground truth source reputation
       record_prediction(reputation_score, ground_truth_reputation)
   ```

4. **Analysis:**
   - ROC curve: Can reputation score predict source quality?
   - Correlation with fact-checker verdicts
   - Coverage: % of images with usable search results

#### Expected Performance Targets

| Metric | Minimum | Target | Stretch |
|--------|---------|--------|---------|
| ROC AUC (high vs. low reputation) | 0.65 | 0.75 | 0.85 |
| Coverage (images with results) | 60% | 75% | 90% |
| Correlation with fact-checker verdicts | 0.40 | 0.55 | 0.70 |

**Rationale:** Reverse search is noisy and coverage-limited. Moderate discrimination is realistic.

#### Known Limitations

- Many medical images lack identifiable matches
- Stock photos appear on both credible and non-credible sites
- Recent misinformation may not yet appear in search indexes

### 4.4 Genealogy Consistency Signal Validation

**Hypothesis:** Provenance tracking can detect image reuse and context changes.

#### Validation Protocol

1. **Dataset:** Dataset D (temporal provenance cases) + manually tracked image reuse
2. **Ground Truth:**
   - Consistent: Image used in same context repeatedly
   - Inconsistent: Image repurposed for different claims
3. **Procedure:**
   ```python
   for image, usage_history in dataset:
       provenance = provenance_service.build_provenance(image)
       consistency_score = compute_genealogy_consistency(provenance)
       
       # Compare to ground truth usage consistency
       record_prediction(consistency_score, ground_truth_consistency)
   ```

4. **Analysis:**
   - Binary classification: Consistent vs. inconsistent
   - Provenance chain integrity: % with complete hash chains
   - Temporal analysis: Does reuse over time correlate with inconsistency?

#### Expected Performance Targets

| Metric | Minimum | Target | Stretch |
|--------|---------|--------|---------|
| Accuracy (consistent vs. inconsistent) | 60% | 70% | 80% |
| Chain completion rate | 70% | 85% | 95% |

**Rationale:** Provenance tracking is deterministic but limited by data availability. Most validation focuses on implementation correctness.

---

## 5. Integrated Score Validation

**Hypothesis:** The weighted combination of contextual signals outperforms any individual signal.

### 5.1 End-to-End Validation Protocol

1. **Dataset:** Combined test set (stratified sample from all datasets)
   - 300 aligned pairs (positive class)
   - 300 misaligned pairs (negative class)
   - 100 unclear/ambiguous pairs (excluded from binary metrics)

2. **Ground Truth:** Expert consensus labels (2+ medical professionals)

3. **Procedure:**
   ```python
   for image, claim, ground_truth in test_set:
       # Run full agentic workflow
       agent = MedContextAgent()
       result = agent.run(
           image_bytes=image,
           context=claim
       )
       
       # Extract contextual integrity score
       ci_score = result.synthesis["contextual_integrity"]["score"]
       alignment = result.synthesis["contextual_integrity"]["alignment"]
       
       # Threshold at 0.5 for binary classification
       predicted = "aligned" if ci_score >= 0.5 else "misaligned"
       
       # Record for analysis
       record_prediction(
           predicted=predicted,
           actual=ground_truth,
           score=ci_score,
           signals=result.synthesis["contextual_integrity"]["signals"]
       )
   ```

4. **Analysis:**
   - Confusion matrix and classification report
   - ROC and PR curves
   - Calibration plot
   - Ablation study (remove each signal, recompute)
   - Failure mode taxonomy

### 5.2 Ablation Study

**Question:** How much does each signal contribute to overall performance?

**Method:**
```python
# Baseline: All signals (60% alignment, 15% plausibility, 15% genealogy, 10% source)
baseline_accuracy = evaluate_full_model(test_set)

# Ablation 1: Remove alignment (reweight: 37.5% plausibility, 37.5% genealogy, 25% source)
no_alignment_accuracy = evaluate_without_alignment(test_set)

# Ablation 2: Remove plausibility
no_plausibility_accuracy = evaluate_without_plausibility(test_set)

# Ablation 3: Remove genealogy
no_genealogy_accuracy = evaluate_without_genealogy(test_set)

# Ablation 4: Remove source reputation
no_source_accuracy = evaluate_without_source(test_set)

# Compute contribution of each signal
contribution = {
    "alignment": baseline_accuracy - no_alignment_accuracy,
    "plausibility": baseline_accuracy - no_plausibility_accuracy,
    "genealogy": baseline_accuracy - no_genealogy_accuracy,
    "source": baseline_accuracy - no_source_accuracy,
}
```

**Expected Contributions:**
- **Alignment:** Largest drop (>15%)—primary signal
- **Plausibility:** Moderate drop (5-10%)—supports alignment
- **Genealogy:** Small drop (2-5%)—limited availability
- **Source Reputation:** Small drop (2-5%)—limited coverage

### 5.3 Weight Optimization

**Question:** Are the current weights (60/15/15/10) optimal?

**Method:** Grid search or Bayesian optimization over weight space
```python
from scipy.optimize import differential_evolution

def objective(weights):
    """Maximize F1 score on validation set."""
    alignment_w, plausibility_w, genealogy_w, source_w = weights
    
    # Evaluate on validation set
    predictions = []
    for image, claim, truth in validation_set:
        score = compute_contextual_integrity_score(
            alignment=signals[image]["alignment"],
            plausibility=signals[image]["plausibility"],
            genealogy_consistency=signals[image]["genealogy"],
            source_reputation=signals[image]["source"],
            weights=ContextualIntegrityWeights(
                alignment=alignment_w,
                plausibility=plausibility_w,
                genealogy_consistency=genealogy_w,
                source_reputation=source_w
            )
        )
        predictions.append((score >= 0.5, truth))
    
    return -compute_f1(predictions)  # Negative for minimization

# Constraint: weights sum to 1.0
bounds = [(0.0, 1.0)] * 4
constraints = {"type": "eq", "fun": lambda w: sum(w) - 1.0}

result = differential_evolution(
    objective,
    bounds=bounds,
    constraints=constraints,
    seed=42
)

optimal_weights = result.x
```

**Validation:** 
- Optimize on validation set (70% of data)
- Evaluate on held-out test set (30% of data)
- Report both validation and test performance

---

## 6. Methodology

### 6.1 Dataset Splitting

**Stratified Train/Validation/Test Split:**
- **Training:** 50% (for weight optimization, if needed)
- **Validation:** 20% (for threshold tuning)
- **Test:** 30% (for final evaluation, never seen during development)

**Stratification Variables:**
- Alignment label (aligned / misaligned / unclear)
- Modality (X-ray, CT, MRI, etc.)
- Claim type (diagnosis, treatment, etc.)

### 6.2 Statistical Testing

#### Bootstrap Confidence Intervals
```python
from sklearn.utils import resample

def bootstrap_metric(y_true, y_pred, metric_fn, n_iterations=1000):
    """Compute 95% CI via bootstrap resampling."""
    scores = []
    for i in range(n_iterations):
        # Resample with replacement
        indices = resample(range(len(y_true)), random_state=i)
        y_true_sample = [y_true[i] for i in indices]
        y_pred_sample = [y_pred[i] for i in indices]
        
        # Compute metric
        score = metric_fn(y_true_sample, y_pred_sample)
        scores.append(score)
    
    # Compute percentiles
    lower = np.percentile(scores, 2.5)
    upper = np.percentile(scores, 97.5)
    mean = np.mean(scores)
    
    return {"mean": mean, "lower_ci": lower, "upper_ci": upper}
```

#### McNemar's Test for Classifier Comparison
```python
from statsmodels.stats.contingency_tables import mcnemar

def compare_classifiers(y_true, y_pred1, y_pred2):
    """Test if two classifiers have significantly different performance."""
    # Build contingency table
    correct1 = (y_pred1 == y_true)
    correct2 = (y_pred2 == y_true)
    
    both_correct = sum(correct1 & correct2)
    only1_correct = sum(correct1 & ~correct2)
    only2_correct = sum(~correct1 & correct2)
    both_wrong = sum(~correct1 & ~correct2)
    
    table = [[both_correct, only2_correct],
             [only1_correct, both_wrong]]
    
    result = mcnemar(table, exact=True)
    return result.pvalue
```

### 6.3 Reproducibility Requirements

All validation runs must include:
- **Random Seed:** Fixed for reproducibility (seed=42)
- **Environment Snapshot:** Python version, library versions (requirements.txt)
- **Dataset Version:** SHA256 hash of dataset files
- **Configuration:** All hyperparameters and settings logged
- **Compute Resources:** GPU/CPU specs, inference time per image
- **Results Archive:** Raw predictions, scores, and metadata saved

---

## 7. Expected Baselines

### 7.1 Naive Baselines

#### Random Classifier
- **Accuracy:** 50% (binary), 33% (3-way aligned/partial/misaligned)
- **ROC AUC:** 0.50
- **Purpose:** Sanity check (must exceed random guessing)

#### Majority Class Baseline
- **Method:** Always predict most common class
- **Accuracy:** Depends on class balance (e.g., 60% if 60% aligned)
- **F1 Score:** Poor for minority classes
- **Purpose:** Ensure model captures signal beyond class distribution

#### Text-Only Baseline
- **Method:** Use LLM to judge claim plausibility from text alone (no image)
- **Expected Accuracy:** 55-65% (can detect obviously implausible claims)
- **Purpose:** Validate that visual analysis adds value

### 7.2 Target Performance

Based on task difficulty and literature review:

| Task | Naive Baseline | Text-Only | Target (Image + Text) |
|------|----------------|-----------|------------------------|
| Alignment detection | 50% | 60% | **75%+** |
| Plausibility (3-way) | 33% | 55% | **65%+** |
| Integrated score (binary) | 50% | 60% | **75%+** |
| ROC AUC (integrated) | 0.50 | 0.65 | **0.80+** |

**Rationale:**
- Medical misinformation detection is inherently difficult (expert-level task)
- Ambiguous cases exist where even human experts disagree
- 75% accuracy represents meaningful improvement over baselines
- 80+ ROC AUC indicates strong discrimination ability

### 7.3 Comparison to Pixel Forensics

| Approach | Dataset | Accuracy | ROC AUC | Threat Coverage |
|----------|---------|----------|---------|-----------------|
| Pixel forensics | UCI Tamper | 49.9% | 0.533 | 20% (manipulated images) |
| **Contextual signals** | Image-claim pairs | **75%+ (target)** | **0.80+ (target)** | **87% (authentic images with false context)** |

**Key Differentiation:** Contextual signals address the dominant threat (authentic images with misleading claims), while pixel forensics only detect manipulated images.

---

## 8. Implementation Guide

### 8.1 Validation Script Structure

```python
# scripts/validate_contextual_signals.py

import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

from app.orchestrator.agent import MedContextAgent
from app.clinical.medgemma_client import MedGemmaClient
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


class ContextualSignalsValidator:
    """Validates MedContext contextual signals against ground truth."""
    
    def __init__(self, dataset_path: Path, output_dir: Path):
        self.dataset_path = dataset_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.agent = MedContextAgent()
        self.results = []
        
    def load_dataset(self) -> List[Dict[str, Any]]:
        """Load validation dataset with ground truth labels.
        
        Expected format:
        [
            {
                "image_path": "path/to/image.jpg",
                "claim": "This shows pneumonia",
                "ground_truth": {
                    "alignment": "aligned" | "misaligned" | "partially_aligned" | "unclear",
                    "plausibility": "high" | "medium" | "low",
                    "is_misinformation": true | false
                }
            },
            ...
        ]
        """
        with open(self.dataset_path) as f:
            return json.load(f)
    
    def run_validation(self):
        """Execute validation on full dataset."""
        dataset = self.load_dataset()
        
        print(f"Validating {len(dataset)} image-claim pairs...")
        
        for i, item in enumerate(dataset):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(dataset)}")
            
            # Load image
            image_bytes = Path(item["image_path"]).read_bytes()
            
            # Run MedContext agent
            result = self.agent.run(
                image_bytes=image_bytes,
                context=item["claim"]
            )
            
            # Extract signals and scores
            ci = result.synthesis.get("contextual_integrity", {})
            signals = ci.get("signals", {})
            
            # Record prediction
            self.results.append({
                "image_id": item.get("image_id", item["image_path"]),
                "claim": item["claim"],
                "ground_truth": item["ground_truth"],
                "predicted": {
                    "alignment": ci.get("alignment"),
                    "alignment_score": signals.get("alignment"),
                    "plausibility_score": signals.get("plausibility"),
                    "genealogy_score": signals.get("genealogy_consistency"),
                    "source_score": signals.get("source_reputation"),
                    "overall_score": ci.get("score"),
                },
                "synthesis": result.synthesis,
            })
        
        print("Validation complete!")
    
    def compute_metrics(self) -> Dict[str, Any]:
        """Compute evaluation metrics."""
        # Extract ground truth and predictions
        y_true = []
        y_pred = []
        scores = []
        
        for result in self.results:
            gt = result["ground_truth"]["alignment"]
            pred = result["predicted"]["alignment"]
            score = result["predicted"]["overall_score"]
            
            # Binary mapping: aligned vs. not aligned
            y_true.append(1 if gt == "aligned" else 0)
            y_pred.append(1 if pred == "aligned" else 0)
            scores.append(score if score is not None else 0.5)
        
        # Compute metrics
        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, zero_division=0),
            "recall": recall_score(y_true, y_pred, zero_division=0),
            "f1_score": f1_score(y_true, y_pred, zero_division=0),
            "roc_auc": roc_auc_score(y_true, scores),
        }
        
        # Bootstrap confidence intervals
        metrics_with_ci = {}
        for metric_name, metric_fn in [
            ("accuracy", accuracy_score),
            ("precision", lambda y, p: precision_score(y, p, zero_division=0)),
            ("recall", lambda y, p: recall_score(y, p, zero_division=0)),
            ("f1_score", lambda y, p: f1_score(y, p, zero_division=0)),
        ]:
            ci = self.bootstrap_metric(y_true, y_pred, metric_fn)
            metrics_with_ci[metric_name] = ci
        
        # ROC AUC bootstrap
        roc_ci = self.bootstrap_metric(
            y_true, scores, 
            lambda y, s: roc_auc_score(y, s)
        )
        metrics_with_ci["roc_auc"] = roc_ci
        
        return {
            "metrics": metrics,
            "metrics_with_ci": metrics_with_ci,
            "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
            "classification_report": classification_report(
                y_true, y_pred, 
                target_names=["misaligned", "aligned"],
                output_dict=True
            ),
        }
    
    def bootstrap_metric(self, y_true, y_pred, metric_fn, n_iterations=1000):
        """Compute 95% CI via bootstrap."""
        from sklearn.utils import resample
        
        scores = []
        for i in range(n_iterations):
            indices = resample(range(len(y_true)), random_state=i)
            y_true_sample = [y_true[i] for i in indices]
            y_pred_sample = [y_pred[i] for i in indices]
            
            try:
                score = metric_fn(y_true_sample, y_pred_sample)
                scores.append(score)
            except ValueError:
                # Handle cases where resampling creates all-one-class
                continue
        
        return {
            "mean": float(np.mean(scores)),
            "lower_ci": float(np.percentile(scores, 2.5)),
            "upper_ci": float(np.percentile(scores, 97.5)),
        }
    
    def analyze_signals(self) -> Dict[str, Any]:
        """Analyze individual signal performance."""
        signal_analysis = {}
        
        for signal_name in ["alignment_score", "plausibility_score", 
                            "genealogy_score", "source_score"]:
            # Extract signal values
            y_true = []
            signal_values = []
            
            for result in self.results:
                gt = result["ground_truth"]["alignment"]
                signal_val = result["predicted"].get(signal_name)
                
                if signal_val is not None:
                    y_true.append(1 if gt == "aligned" else 0)
                    signal_values.append(signal_val)
            
            if len(signal_values) > 0:
                # Compute ROC AUC for this signal alone
                try:
                    roc_auc = roc_auc_score(y_true, signal_values)
                except ValueError:
                    roc_auc = None
                
                # Compute mean difference between aligned vs. misaligned
                aligned_vals = [s for s, t in zip(signal_values, y_true) if t == 1]
                misaligned_vals = [s for s, t in zip(signal_values, y_true) if t == 0]
                
                signal_analysis[signal_name] = {
                    "roc_auc": roc_auc,
                    "mean_aligned": float(np.mean(aligned_vals)) if aligned_vals else None,
                    "mean_misaligned": float(np.mean(misaligned_vals)) if misaligned_vals else None,
                    "separation": float(np.mean(aligned_vals) - np.mean(misaligned_vals)) if aligned_vals and misaligned_vals else None,
                    "coverage": len(signal_values) / len(self.results),
                }
        
        return signal_analysis
    
    def ablation_study(self) -> Dict[str, Any]:
        """Measure contribution of each signal via ablation."""
        from app.metrics.integrity import compute_contextual_integrity_score
        
        # Baseline: All signals
        y_true = []
        y_pred_baseline = []
        
        for result in self.results:
            gt = result["ground_truth"]["alignment"]
            score = result["predicted"]["overall_score"]
            
            y_true.append(1 if gt == "aligned" else 0)
            y_pred_baseline.append(1 if score >= 0.5 else 0)
        
        baseline_acc = accuracy_score(y_true, y_pred_baseline)
        
        # Ablation: Remove each signal
        ablation_results = {"baseline": baseline_acc}
        
        for signal_to_remove in ["alignment", "plausibility", "genealogy", "source"]:
            y_pred_ablated = []
            
            for result in self.results:
                signals = result["predicted"]
                
                # Recompute score without this signal
                signal_values = {
                    "alignment": signals.get("alignment_score"),
                    "plausibility": signals.get("plausibility_score"),
                    "genealogy_consistency": signals.get("genealogy_score"),
                    "source_reputation": signals.get("source_score"),
                }
                
                # Set removed signal to None
                if signal_to_remove == "alignment":
                    signal_values["alignment"] = None
                elif signal_to_remove == "plausibility":
                    signal_values["plausibility"] = None
                elif signal_to_remove == "genealogy":
                    signal_values["genealogy_consistency"] = None
                elif signal_to_remove == "source":
                    signal_values["source_reputation"] = None
                
                # Recompute score (weights will auto-adjust)
                ablated_score = compute_contextual_integrity_score(**signal_values)
                y_pred_ablated.append(1 if ablated_score >= 0.5 else 0)
            
            ablated_acc = accuracy_score(y_true, y_pred_ablated)
            contribution = baseline_acc - ablated_acc
            
            ablation_results[f"without_{signal_to_remove}"] = {
                "accuracy": ablated_acc,
                "contribution": contribution,
            }
        
        return ablation_results
    
    def generate_plots(self):
        """Generate visualization plots."""
        # Confusion matrix
        self.plot_confusion_matrix()
        
        # ROC curve
        self.plot_roc_curve()
        
        # Signal distributions
        self.plot_signal_distributions()
        
        # Calibration plot
        self.plot_calibration()
    
    def plot_confusion_matrix(self):
        """Plot confusion matrix heatmap."""
        y_true = [1 if r["ground_truth"]["alignment"] == "aligned" else 0 
                  for r in self.results]
        y_pred = [1 if r["predicted"]["alignment"] == "aligned" else 0 
                  for r in self.results]
        
        cm = confusion_matrix(y_true, y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=["Misaligned", "Aligned"],
                    yticklabels=["Misaligned", "Aligned"])
        plt.title("Contextual Alignment Confusion Matrix")
        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.tight_layout()
        plt.savefig(self.output_dir / "confusion_matrix.png", dpi=300)
        plt.close()
    
    def plot_roc_curve(self):
        """Plot ROC curve."""
        from sklearn.metrics import roc_curve
        
        y_true = [1 if r["ground_truth"]["alignment"] == "aligned" else 0 
                  for r in self.results]
        scores = [r["predicted"]["overall_score"] or 0.5 for r in self.results]
        
        fpr, tpr, thresholds = roc_curve(y_true, scores)
        roc_auc = roc_auc_score(y_true, scores)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, label=f'Contextual Signals (AUC = {roc_auc:.3f})', linewidth=2)
        plt.plot([0, 1], [0, 1], 'k--', label='Random Classifier (AUC = 0.500)')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve: Contextual Integrity Score')
        plt.legend(loc="lower right")
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.output_dir / "roc_curve.png", dpi=300)
        plt.close()
    
    def plot_signal_distributions(self):
        """Plot signal value distributions for aligned vs. misaligned."""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        axes = axes.flatten()
        
        signal_names = ["alignment_score", "plausibility_score", 
                        "genealogy_score", "source_score"]
        signal_labels = ["Alignment", "Plausibility", 
                         "Genealogy Consistency", "Source Reputation"]
        
        for ax, signal_name, label in zip(axes, signal_names, signal_labels):
            aligned_vals = []
            misaligned_vals = []
            
            for result in self.results:
                gt = result["ground_truth"]["alignment"]
                val = result["predicted"].get(signal_name)
                
                if val is not None:
                    if gt == "aligned":
                        aligned_vals.append(val)
                    else:
                        misaligned_vals.append(val)
            
            if aligned_vals and misaligned_vals:
                ax.hist(aligned_vals, bins=20, alpha=0.6, label="Aligned", color="green")
                ax.hist(misaligned_vals, bins=20, alpha=0.6, label="Misaligned", color="red")
                ax.axvline(np.mean(aligned_vals), color="darkgreen", linestyle="--", 
                          label=f"Aligned Mean: {np.mean(aligned_vals):.2f}")
                ax.axvline(np.mean(misaligned_vals), color="darkred", linestyle="--",
                          label=f"Misaligned Mean: {np.mean(misaligned_vals):.2f}")
                ax.set_xlabel(f"{label} Score")
                ax.set_ylabel("Frequency")
                ax.set_title(f"{label} Signal Distribution")
                ax.legend()
                ax.grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / "signal_distributions.png", dpi=300)
        plt.close()
    
    def plot_calibration(self):
        """Plot calibration curve."""
        from sklearn.calibration import calibration_curve
        
        y_true = [1 if r["ground_truth"]["alignment"] == "aligned" else 0 
                  for r in self.results]
        scores = [r["predicted"]["overall_score"] or 0.5 for r in self.results]
        
        prob_true, prob_pred = calibration_curve(y_true, scores, n_bins=10)
        
        plt.figure(figsize=(8, 6))
        plt.plot(prob_pred, prob_true, marker='o', linewidth=2, label="Contextual Signals")
        plt.plot([0, 1], [0, 1], 'k--', label="Perfect Calibration")
        plt.xlabel("Predicted Probability")
        plt.ylabel("Observed Frequency")
        plt.title("Calibration Plot: Contextual Integrity Score")
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.output_dir / "calibration.png", dpi=300)
        plt.close()
    
    def generate_report(self):
        """Generate comprehensive validation report."""
        metrics = self.compute_metrics()
        signal_analysis = self.analyze_signals()
        ablation = self.ablation_study()
        
        report = {
            "dataset": {
                "path": str(self.dataset_path),
                "n_samples": len(self.results),
            },
            "overall_performance": metrics,
            "signal_analysis": signal_analysis,
            "ablation_study": ablation,
            "raw_results": self.results,
        }
        
        # Save report
        report_path = self.output_dir / "contextual_signals_validation_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{'='*60}")
        print("CONTEXTUAL SIGNALS VALIDATION REPORT")
        print(f"{'='*60}\n")
        
        print(f"Dataset: {len(self.results)} samples\n")
        
        print("Overall Performance (with 95% CI):")
        for metric, values in metrics["metrics_with_ci"].items():
            print(f"  {metric:15s}: {values['mean']:.3f} [{values['lower_ci']:.3f}, {values['upper_ci']:.3f}]")
        
        print("\nSignal Analysis (Individual ROC AUC):")
        for signal, analysis in signal_analysis.items():
            if analysis["roc_auc"] is not None:
                print(f"  {signal:25s}: {analysis['roc_auc']:.3f} (coverage: {analysis['coverage']:.1%})")
        
        print("\nAblation Study (Signal Contribution):")
        for key, value in ablation.items():
            if key == "baseline":
                print(f"  {key:25s}: {value:.3f}")
            else:
                print(f"  {key:25s}: {value['accuracy']:.3f} (contribution: {value['contribution']:+.3f})")
        
        print(f"\nFull report saved to: {report_path}")
        print(f"Plots saved to: {self.output_dir}/")
        print(f"{'='*60}\n")
        
        return report


def main():
    parser = argparse.ArgumentParser(
        description="Validate MedContext contextual signals"
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Path to validation dataset JSON"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("validation_results/contextual_signals"),
        help="Output directory for results"
    )
    
    args = parser.parse_args()
    
    validator = ContextualSignalsValidator(
        dataset_path=args.dataset,
        output_dir=args.output_dir
    )
    
    validator.run_validation()
    validator.generate_plots()
    validator.generate_report()


if __name__ == "__main__":
    main()
```

### 8.2 Dataset Preparation Scripts

You'll also need scripts to:
1. **Curate datasets** from medical literature
2. **Collect ground truth labels** from expert annotators
3. **Format datasets** into the expected JSON structure
4. **Split datasets** into train/validation/test

See `scripts/prepare_contextual_validation_dataset.py` (to be created).

### 8.3 Running Validation

```bash
# 1. Install dependencies
uv venv && uv run pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Add: MEDGEMMA_PROVIDER=vertex (or huggingface)
# Add: MEDGEMMA_HF_TOKEN=hf_your_token (if using HuggingFace)

# 3. Prepare validation dataset (see Section 2)
python scripts/prepare_contextual_validation_dataset.py \
  --source-dir data/medical_images \
  --output validation_datasets/contextual_signals_v1.json

# 4. Run validation
python scripts/validate_contextual_signals.py \
  --dataset validation_datasets/contextual_signals_v1.json \
  --output-dir validation_results/contextual_signals_v1

# 5. View results
cat validation_results/contextual_signals_v1/contextual_signals_validation_report.json
open validation_results/contextual_signals_v1/roc_curve.png
```

---

## 9. Reproducibility

### 9.1 Environment Specification

```bash
# Python version
python --version  # 3.12+

# Dependencies
uv pip freeze > validation_environment.txt

# System info
uname -a
```

### 9.2 Dataset Versioning

```bash
# Compute dataset hash
sha256sum validation_datasets/contextual_signals_v1.json > dataset_hash.txt

# Include in results
echo "dataset_sha256: $(cat dataset_hash.txt)" >> validation_results/metadata.txt
```

### 9.3 Random Seeding

All random operations use fixed seeds:
- Bootstrap resampling: `seed=42`
- Dataset splitting: `seed=42`
- Model inference: Deterministic (no sampling)

### 9.4 Results Archive

Each validation run produces:
```
validation_results/contextual_signals_v1/
├── contextual_signals_validation_report.json  # Full results
├── confusion_matrix.png                       # Confusion matrix plot
├── roc_curve.png                              # ROC curve
├── signal_distributions.png                   # Signal histograms
├── calibration.png                            # Calibration plot
├── metadata.txt                               # Environment info
└── raw_predictions.jsonl                      # Individual predictions
```

---

## Conclusion

This validation framework provides a rigorous, reproducible approach to evaluating MedContext's contextual signals. By targeting the 87% of medical misinformation cases where authentic images are misused, this validation directly addresses the real-world threat distribution.

**Key Differentiators:**
1. **Ground Truth Datasets:** Expert-annotated image-claim pairs with verified labels
2. **Multi-Signal Analysis:** Individual and integrated signal validation
3. **Ablation Studies:** Quantify each signal's contribution
4. **Statistical Rigor:** Bootstrap CIs, hypothesis testing, calibration analysis
5. **Reproducibility:** Fixed seeds, versioned datasets, environment snapshots

**Next Steps:**
1. Curate Dataset A (medical image-caption pairs) with expert annotations
2. Collect Dataset B (social media misinformation corpus) from fact-checkers
3. Implement validation scripts and run pilot validation
4. Iterate on signal weights based on empirical results
5. Prepare validation results for competition submission and deployment partner (HERO Lab, UBC)

**Expected Outcome:** Demonstrate that contextual signals achieve 75%+ accuracy in detecting medical image misinformation, far exceeding pixel forensics (~50%) and addressing the dominant real-world threat.

---

**Document Version:** 1.0  
**Created:** January 31, 2026  
**Status:** Design complete, ready for implementation
