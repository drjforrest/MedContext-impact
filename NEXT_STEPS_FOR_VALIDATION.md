# Validating MedContext with Med-MMHL and AMMeBa: A Comprehensive Strategy

# Validating MedContext with Med-MMHL and AMMeBa: A Comprehensive Strategy

Based on my examination of your MedContext project and analysis of the Med-MMHL and AMMeBa datasets, I can provide you with a detailed validation approach. Your system's core thesis—that authentic medical images with misleading context represent the dominant threat (~80%)—aligns perfectly with what these datasets measure, but each requires different adaptation strategies.

## Understanding the Dataset Characteristics

### Med-MMHL Dataset Structure

From the paper and documentation, Med-MMHL contains:[1][2]

**Multimodal Fake News Detection Task:**

- **Real claims:** 643 text items, 641 with images, 749 total images
- **Fake claims:** 1,135 text items, 1,102 with images, 1,102 images
- **Total image-claim pairs:** ~1,778 multimodal pairs

**Critical Limitation:** The authors explicitly do not categorize images into "medical" (radiology, histology, clinical photographs) versus decorative or screenshot types. They only describe qualitative patterns noting that:[1]

- Real news articles often use decorative images from the internet
- Fake news articles frequently use screenshots of social media or videos
- Fact-checking sources vary (AFPFactCheck uses screenshots, CheckYourFact and PolitiFact use decorative images)

**Image Filtering Applied:** To avoid trivial cues in their multimodal benchmark, they selected true claims from AFP Fact Check and false claims from CheckYourFact and PolitiFact. This suggests approximately **643 + 1,135 = 1,778 filtered multimodal claim pairs** are available for your validation.[1]

### AMMeBa Dataset Structure

AMMeBa is fundamentally different—it's a large-scale survey of **context manipulation** which directly validates your thesis:[3][4][5][6][7]

**Dataset Characteristics:**

- **135,838 fact-checked claims** (1995-November 2023)
- Focus: Media-based misinformation, primarily images
- **Key Finding:** Context manipulations (authentic images with false claims) are the **dominant form** of media-based misinformation, not pixel-level manipulations[7][8]

**Image Typology:**

- **Basic images:** Coherent photographic images without overlays
- **Complex images:** Screenshots, graphical elements, compositions
- **Text-based images:** Images with text conveying misinformation directly

**Manipulation Classification:**

- **Content manipulations:** Direct image alterations (deepfakes, photo manipulation)
- **Context manipulations:** False claims about image context/origin while image remains authentic (this is your 80% threat)
- **AI-generated content:** Rose dramatically in Spring 2023, but still not dominant as of November 2023[4][7]

**Important:** AMMeBa is not limited to medical misinformation—it spans all domains. You would need to filter for health/medical-related claims to create a relevant validation subset.

## Validation Strategy for MedContext

### Phase 1: Med-MMHL Validation (Multimodal Claim Verification)

**Objective:** Validate MedContext's ability to detect contextual misalignment between medical images and claims

#### Step 1: Dataset Acquisition and Preprocessing

```python
# Download Med-MMHL from GitHub
# https://github.com/styxsys0927/Med-MMHL

# Expected structure after download:
# med-mmhl/
#   multimodal_claims/
#     real_claims.json  # 643 items with 749 images
#     fake_claims.json  # 1,135 items with 1,102 images
```

**Image Categorization (Manual Step Required):**

Since the dataset doesn't provide medical vs. non-medical image labels, you must:

1. **Sample and annotate** a representative subset (e.g., 200-300 claim-image pairs)
2. **Categorize each image** as:
   - **Type A: True Medical Images** (radiographs, CT, MRI, histology, clinical photos, endoscopy)
   - **Type B: Decorative/Stock Medical** (stock photos of doctors, hospitals, medical equipment)
   - **Type C: Screenshots** (social media posts, website captures)
   - **Type D: Non-medical** (general news images, unrelated photos)

3. **Create annotations file:**

```json
{
  "claim_id": "med_mmhl_001",
  "image_type": "radiology_xray",
  "is_authentic_medical_image": true,
  "claim_veracity": "false",
  "expected_medcontext_dimension": "alignment" // veracity, alignment, or pixel_authenticity
}
```

#### Step 2: Validation Protocol

**A. Define Evaluation Dimensions**

MedContext has three assessment layers that map to different aspects of Med-MMHL:[9][10]

| MedContext Layer                                          | Med-MMHL Application                                 | Expected Performance                       |
| --------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------ |
| **Layer 1: Pixel Authenticity** (format-routed forensics) | Limited utility—most images are authentic JPEGs/PNGs | Baseline: should mark most as authentic    |
| **Layer 2: Veracity** (MedGemma on claim alone)           | Assess claim plausibility without image              | Target: 61-65% (matches PoJ 3 results)[10] |
| **Layer 3: Alignment** (MedGemma on image-claim pair)     | Core validation: does image support claim?           | Target: 56-70%                             |

**B. Experimental Design**

```python
# Validation script structure
from medcontext.orchestrator import MedContextOrchestrator
from med_mmhl_loader import load_multimodal_claims
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score

def validate_medcontext_on_medmmhl():
    """
    Validate MedContext on Med-MMHL multimodal claim dataset
    """
    # Load dataset
    claims = load_multimodal_claims(
        real_path="data/med-mmhl/multimodal_claims/real_claims.json",
        fake_path="data/med-mmhl/multimodal_claims/fake_claims.json",
        annotations_path="data/med-mmhl/image_type_annotations.json"  # Your manual annotations
    )

    # Filter for medical images only (Type A)
    medical_image_claims = [
        c for c in claims
        if c['annotations']['is_authentic_medical_image']
    ]

    print(f"Total claims: {len(claims)}")
    print(f"Medical image claims: {len(medical_image_claims)}")

    # Initialize orchestrator
    orchestrator = MedContextOrchestrator()

    # Run predictions
    predictions = []
    ground_truth = []

    for claim in medical_image_claims:
        result = orchestrator.analyze(
            image_path=claim['image_path'],
            context_text=claim['claim_text']
        )

        # Extract verdicts
        predictions.append({
            'pixel_authentic': result['forensics']['verdict'] == 'AUTHENTIC',
            'claim_veracity': result['semantic']['veracity_score'] > 0.5,
            'alignment': result['semantic']['alignment_score'] > 0.5,
            'overall_verdict': result['overall_verdict']  # ALIGNED, MISALIGNED, UNCERTAIN
        })

        ground_truth.append({
            'is_fake_claim': claim['label'] == 'fake',
            'expected_misalignment': claim['label'] == 'fake'  # Fake claims should misalign
        })

    # Compute metrics
    return compute_three_dimensional_metrics(predictions, ground_truth)

def compute_three_dimensional_metrics(preds, truth):
    """
    Compute metrics for each MedContext dimension
    """
    # Dimension 1: Pixel Authenticity (should be high for Med-MMHL)
    pixel_acc = np.mean([p['pixel_authentic'] for p in preds])

    # Dimension 2: Veracity (claim plausibility)
    veracity_preds = [not p['claim_veracity'] for p in preds]  # Invert: high score = plausible
    veracity_truth = [t['is_fake_claim'] for t in truth]
    veracity_metrics = precision_recall_fscore_support(
        veracity_truth, veracity_preds, average='binary'
    )

    # Dimension 3: Alignment (image-claim consistency)
    alignment_preds = [not p['alignment'] for p in preds]  # Invert: high score = aligned
    alignment_truth = [t['expected_misalignment'] for t in truth]
    alignment_metrics = precision_recall_fscore_support(
        alignment_truth, alignment_preds, average='binary'
    )

    return {
        'pixel_authenticity': {
            'mean_authentic_rate': pixel_acc,
            'interpretation': f"{pixel_acc:.1%} marked as pixel-authentic (expected: >90% for Med-MMHL)"
        },
        'veracity': {
            'accuracy': accuracy_score(veracity_truth, veracity_preds),
            'precision': veracity_metrics[0],
            'recall': veracity_metrics[1],
            'f1': veracity_metrics[2]
        },
        'alignment': {
            'accuracy': accuracy_score(alignment_truth, alignment_preds),
            'precision': alignment_metrics[0],
            'recall': alignment_metrics[1],
            'f1': alignment_metrics[2]
        }
    }
```

**C. Bootstrap Confidence Intervals**

Following your validation methodology:[10]

```python
def bootstrap_validation(claims, n_iterations=1000):
    """
    Bootstrap resampling for 95% confidence intervals
    """
    from sklearn.utils import resample

    metrics_dist = {
        'veracity_acc': [],
        'alignment_acc': [],
        'veracity_f1': [],
        'alignment_f1': []
    }

    for i in range(n_iterations):
        # Resample with replacement
        sample = resample(claims, n_samples=len(claims), random_state=i)

        # Run validation
        results = validate_medcontext_on_medmmhl_subset(sample)

        # Store metrics
        metrics_dist['veracity_acc'].append(results['veracity']['accuracy'])
        metrics_dist['alignment_acc'].append(results['alignment']['accuracy'])
        metrics_dist['veracity_f1'].append(results['veracity']['f1'])
        metrics_dist['alignment_f1'].append(results['alignment']['f1'])

    # Compute 95% CI
    ci_results = {}
    for metric, values in metrics_dist.items():
        ci_results[metric] = {
            'mean': np.mean(values),
            'ci_lower': np.percentile(values, 2.5),
            'ci_upper': np.percentile(values, 97.5),
            'std': np.std(values)
        }

    return ci_results
```

#### Step 3: Expected Results and Interpretation

Based on your current validation results and Med-MMHL characteristics:[9][10]

| Metric                      | Expected Range | Interpretation                                                             |
| --------------------------- | -------------- | -------------------------------------------------------------------------- |
| **Pixel Authenticity Rate** | 85-95%         | Most Med-MMHL images are authentic; format-routed forensics should confirm |
| **Veracity Accuracy**       | 60-70%         | Claim plausibility assessment (matches your 61.3% on BTD/UCI)[10]          |
| **Alignment Accuracy**      | 55-65%         | Image-claim consistency (matches your 56.9% baseline)[10]                  |
| **Overall F1 (3-class)**    | 50-60%         | ALIGNED/MISALIGNED/UNCERTAIN classification                                |

**Key Validation Points:**

1. **Pixel forensics should NOT drive verdicts** on Med-MMHL (authentic images dominate)
2. **Contextual analysis (Layers 2+3) should differentiate** true vs. false claims
3. **Medical image subset performance** should exceed decorative image performance (MedGemma's medical training)

### Phase 2: AMMeBa Validation (Context Manipulation Detection)

**Objective:** Validate MedContext's core thesis using the largest real-world context manipulation dataset

#### Step 1: Dataset Filtering for Medical Domain

AMMeBa is cross-domain, so you must filter for health/medical claims:

```python
import pandas as pd

def filter_ammeba_medical_claims(ammeba_path):
    """
    Filter AMMeBa for medical/health-related claims
    """
    # Load AMMeBa annotations
    claims = pd.read_csv(f"{ammeba_path}/ammeba_annotations.csv")

    # Define medical keywords (expand as needed)
    medical_keywords = [
        'vaccine', 'covid', 'virus', 'disease', 'treatment', 'medication',
        'hospital', 'doctor', 'health', 'medical', 'cancer', 'diagnosis',
        'symptom', 'patient', 'clinical', 'pharmaceutical', 'drug'
    ]

    # Filter claims
    medical_claims = claims[
        claims['claim_text'].str.lower().str.contains('|'.join(medical_keywords), na=False)
    ]

    print(f"Total AMMeBa claims: {len(claims)}")
    print(f"Medical subset: {len(medical_claims)} ({len(medical_claims)/len(claims):.1%})")

    return medical_claims
```

**Expected Medical Subset Size:** ~5-15% of 135,838 claims = **6,800-20,000 medical claims**

#### Step 2: Manipulation Type Analysis

AMMeBa categorizes manipulation types—this is critical for validating your thesis:[8][4][7]

```python
def analyze_ammeba_manipulation_types(medical_claims):
    """
    Analyze distribution of manipulation types in medical subset
    """
    manipulation_counts = medical_claims['manipulation_type'].value_counts()

    # Expected distribution based on AMMeBa findings:
    # - Context manipulations: 60-70% (your core threat)
    # - Content manipulations: 15-25%
    # - AI-generated: 5-15% (rising since 2023)
    # - Text-based: 5-10%

    return {
        'context_manipulation': manipulation_counts.get('context', 0),
        'content_manipulation': manipulation_counts.get('content', 0),
        'ai_generated': manipulation_counts.get('ai_generated', 0),
        'text_based': manipulation_counts.get('text_based', 0)
    }
```

#### Step 3: Stratified Validation by Manipulation Type

**Critical Insight:** MedContext should perform **best on context manipulations** (your design target) and **worst on content manipulations** (pixel-level changes):

```python
def stratified_ammeba_validation(medical_claims):
    """
    Validate MedContext separately for each manipulation type
    """
    results_by_type = {}

    for manip_type in ['context', 'content', 'ai_generated', 'text_based']:
        subset = medical_claims[medical_claims['manipulation_type'] == manip_type]

        if len(subset) < 50:
            print(f"Skipping {manip_type}: insufficient samples ({len(subset)})")
            continue

        # Run MedContext
        predictions = []
        for idx, claim in subset.iterrows():
            result = medcontext.analyze(
                image_path=claim['image_path'],
                context_text=claim['claim_text']
            )
            predictions.append(result)

        # Compute metrics
        results_by_type[manip_type] = {
            'n_samples': len(subset),
            'accuracy': compute_accuracy(predictions, subset['is_misinformation']),
            'alignment_score': np.mean([p['semantic']['alignment_score'] for p in predictions]),
            'pixel_authentic_rate': np.mean([p['forensics']['verdict'] == 'AUTHENTIC' for p in predictions])
        }

    return results_by_type
```

**Expected Performance Hierarchy:**

| Manipulation Type        | Expected Accuracy | Rationale                                                                           |
| ------------------------ | ----------------- | ----------------------------------------------------------------------------------- |
| **Context manipulation** | 65-75%            | MedContext's design target; semantic layers excel                                   |
| **Text-based images**    | 60-70%            | MedGemma can analyze embedded text claims                                           |
| **Content manipulation** | 45-60%            | Pixel forensics detects some; semantic helps with implausibility                    |
| **AI-generated (2023+)** | 50-65%            | Mixed signals: pixel forensics may detect artifacts; semantic assesses plausibility |

#### Step 4: Temporal Analysis (Optional Advanced Validation)

AMMeBa spans 1995-2023, enabling temporal validation:[5][3]

```python
def temporal_validation(medical_claims):
    """
    Analyze MedContext performance across time periods
    """
    # Define periods
    periods = {
        'pre_covid': medical_claims[medical_claims['date'] < '2020-01-01'],
        'covid_era': medical_claims[(medical_claims['date'] >= '2020-01-01') &
                                    (medical_claims['date'] < '2023-01-01')],
        'ai_era': medical_claims[medical_claims['date'] >= '2023-01-01']  # Post-ChatGPT/DALL-E 3
    }

    results = {}
    for period_name, subset in periods.items():
        results[period_name] = validate_medcontext_on_ammeba_subset(subset)

    # Expected finding: Performance should remain stable across periods
    # (validates that MedContext doesn't rely on outdated manipulation signatures)
    return results
```

### Phase 3: Combined Dataset Validation Report

#### Reporting Structure

Create a comprehensive validation document:

```markdown
# MedContext Validation Report: Med-MMHL and AMMeBa

## Executive Summary

- **Med-MMHL (Medical Multimodal):** [N] medical image-claim pairs
- **AMMeBa (Context Manipulation):** [N] medical misinformation claims
- **Validation Method:** Bootstrap resampling (1,000 iterations), stratified by manipulation type

## Results

### Med-MMHL Performance (95% CI)

| Dimension               | Accuracy    | Precision | Recall | F1 Score |
| ----------------------- | ----------- | --------- | ------ | -------- |
| Pixel Authenticity      | [X]% [[CI]] | -         | -      | -        |
| Veracity (claim alone)  | [X]% [[CI]] | [X]%      | [X]%   | [X]%     |
| Alignment (image+claim) | [X]% [[CI]] | [X]%      | [X]%   | [X]%     |

**Key Finding:** [Statement about whether contextual layers outperform pixel forensics]

### AMMeBa Performance by Manipulation Type

| Type                 | N Samples | Accuracy [95% CI] | Interpretation                        |
| -------------------- | --------- | ----------------- | ------------------------------------- |
| Context manipulation | [N]       | [X]% [[CI]]       | ✅ Strong (design target)             |
| Content manipulation | [N]       | [X]% [[CI]]       | ⚠️ Moderate (pixel forensics limited) |
| AI-generated         | [N]       | [X]% [[CI]]       | [Status]                              |

**Validation of Core Thesis:**
Context manipulations comprise [X]% of medical misinformation in AMMeBa.
MedContext achieves [X]% accuracy on context manipulations vs. [Y]% on content manipulations,
confirming optimization for the dominant real-world threat.

## Comparison to Baseline Methods

| Method                           | Med-MMHL F1 | AMMeBa Context Acc | Notes                        |
| -------------------------------- | ----------- | ------------------ | ---------------------------- |
| MedContext (ours)                | [X]%        | [X]%               | Three-dimensional assessment |
| CLIP (multimodal baseline)       | 92.7%\*     | -                  | From Med-MMHL paper          |
| VisualBERT (multimodal baseline) | 91.9%\*     | -                  | From Med-MMHL paper          |

\*Reported in Med-MMHL paper for full dataset (not medical-image subset)

## Limitations

1. **Med-MMHL:** Manual annotation required to identify medical images vs. decorative
2. **AMMeBa:** Cross-domain dataset; medical subset size [X]% of total
3. **Both:** Claims may not have associated ground-truth veracity labels beyond fact-check verdicts
```

## Practical Implementation Steps

### Week 1: Data Preparation

**Day 1-2: Med-MMHL**

- [ ] Clone Med-MMHL repository: `git clone https://github.com/styxsys0927/Med-MMHL`
- [ ] Download multimodal claim data (follow repo instructions)
- [ ] Sample 300 claim-image pairs for manual annotation
- [ ] Create annotation schema (medical/decorative/screenshot/other)

**Day 3-4: AMMeBa**

- [ ] Download AMMeBa dataset from Google Research
- [ ] Filter for medical keywords (use NLP term extraction for comprehensive coverage)
- [ ] Analyze manipulation type distribution
- [ ] Sample stratified subset (200 per manipulation type if available)

**Day 5-7: Integration**

- [ ] Write data loaders for both datasets
- [ ] Create unified evaluation framework
- [ ] Set up bootstrap resampling infrastructure

### Week 2: Validation Execution

**Day 8-10: Med-MMHL Validation**

- [ ] Run MedContext on all multimodal claims
- [ ] Execute 1,000 bootstrap iterations
- [ ] Generate performance plots (ROC, confusion matrices, CI intervals)

**Day 11-13: AMMeBa Validation**

- [ ] Stratified validation by manipulation type
- [ ] Temporal analysis (optional)
- [ ] Cross-dataset generalization test

**Day 14: Analysis & Reporting**

- [ ] Compile validation report
- [ ] Update VALIDATION.md with new results
- [ ] Create visualizations for documentation

## Critical Considerations

### 1. **Image Type Annotation is Essential**

Med-MMHL does not distinguish medical images from decorative ones. Your validation **must** include manual annotation of a representative sample to:[1]

- Report "medical image subset" performance separately
- Demonstrate that MedGemma's medical training benefits medical images specifically
- Avoid inflated metrics from trivial decorative image classification

### 2. **Ground Truth Alignment with MedContext Dimensions**

Your three-dimensional framework requires careful mapping:

| Dataset  | Has Veracity Labels?     | Has Alignment Labels?                                     | Has Pixel Manipulation Labels?             |
| -------- | ------------------------ | --------------------------------------------------------- | ------------------------------------------ |
| Med-MMHL | ✅ (claim truth)         | ⚠️ (implicit: fake claims likely misalign with any image) | ❌ (images assumed authentic)              |
| AMMeBa   | ✅ (fact-check verdicts) | ✅ (manipulation type indicates context vs. content)      | ⚠️ (manipulation type partially indicates) |

**Implication:** You may need to define "alignment ground truth" based on reasonable assumptions:

- Med-MMHL: Fake claims with real images = misaligned (unless claim is decorative/generic)
- AMMeBa: Context manipulation = misalignment by definition; content manipulation = pixel tampering but claim may still be true

### 3. **Handling Uncertain Verdicts**

Your current system outputs three classes (ALIGNED, MISALIGNED, UNCERTAIN). For binary datasets:[10]

- **Conservative mapping:** UNCERTAIN → MISALIGNED (maximizes recall, penalizes precision)
- **Optimistic mapping:** UNCERTAIN → ALIGNED (maximizes precision, penalizes recall)
- **Best practice:** Report both mappings + three-class macro F1 for full transparency

### 4. **Baseline Comparisons**

Med-MMHL paper reports baselines:[1]

- CLIP: 96.3% accuracy, 92.7% F1
- VisualBERT: 96.1% accuracy, 91.9% F1

**Important:** These are on the **full multimodal fake news task**, not filtered for medical images. Your comparison should:

1. Report their baselines on your medical-image subset
2. Acknowledge different task formulations (binary fake news vs. three-dimensional contextual assessment)
3. Emphasize MedContext's explainability advantage (three separate scores vs. black-box verdict)

## Conclusion and Recommendations

### Recommended Validation Approach

**Primary Validation:** AMMeBa medical subset stratified by manipulation type

- **Rationale:** Directly measures your core thesis (context manipulation dominance)
- **Expected outcome:** High performance on context manipulations validates design
- **Sample size:** Aim for 500-1,000 medical context manipulation cases minimum

**Secondary Validation:** Med-MMHL medical-image subset

- **Rationale:** Tests multimodal claim verification in medical domain
- **Expected outcome:** Semantic layers outperform pixel forensics
- **Sample size:** 200-400 manually annotated medical image-claim pairs

### Success Criteria

Your validation should demonstrate:

1. **✅ Context manipulation performance > content manipulation performance** (validates thesis)
2. **✅ Medical image performance ≥ non-medical performance** (validates MedGemma benefit)
3. **✅ Three-dimensional assessment provides interpretable signals** (pixel/veracity/alignment)
4. **✅ Performance stable across time periods** (no overfitting to historical manipulation patterns)

### Next Steps

1. **Immediate:** Download both datasets and assess medical subset sizes
2. **Week 1:** Complete image type annotations for Med-MMHL sample
3. **Week 2:** Run validation experiments with bootstrap CI
4. **Week 3:** Write validation report and update documentation[11][9]

This validation strategy will provide rigorous empirical evidence that MedContext is optimized for the real-world medical misinformation threat landscape, distinguishing your system from competitors focused on synthetic manipulation benchmarks.

Sources
[1] Med-MMHL: A Multi-Modal Dataset for Detecting Human https://arxiv.org/html/2306.08871v1
[2] Med-MMHL: A Multi-Modal Dataset for Detecting Human https://arxiv.org/abs/2306.08871
[3] AMMeBa: Survey of Media Misinformation https://www.emergentmind.com/papers/2405.11697
[4] [Literature Review] AMMeBa: A Large-Scale Survey and ... https://www.themoonlight.io/en/review/ammeba-a-large-scale-survey-and-dataset-of-media-based-misinformation-in-the-wild
[5] [2405.11697] AMMeBa: A Large-Scale Survey and Dataset ... https://arxiv.org/abs/2405.11697
[6] AMMEBA: A Large-Scale Survey and Dataset of Media- ... https://research.google/pubs/ammeba-a-large-scale-survey-and-dataset-of-media-based-misinformation-in-the-wild/
[7] After more than two years of work, we're making "AMMeBa" public. It's is… | Nicholas Dufour https://www.linkedin.com/posts/nicholas-dufour-63b91047_after-more-than-two-years-of-work-were-activity-7199021765442908161-yzCf
[8] [Revisión de artículo] AMMeBa: A Large-Scale Survey and Dataset of Media-Based Misinformation In-The-Wild https://www.themoonlight.io/es/review/ammeba-a-large-scale-survey-and-dataset-of-media-based-misinformation-in-the-wild
[10] Med-MMHL: A Multi-Modal Dataset for Detecting Human- and LLM ... https://sanghani.cs.vt.edu/research/publications/2023/med-mmhl-a-multi-modal-dataset-for-detecting-human-and-llm-generated-misinformation-in-the-medical-domain.html
[11] A Real-world Dataset and Benchmark For Foundation ... http://www.qingyuan.sjtu.edu.cn/uploads/20250210/c889df774d6684138640983629009a8e.pdf
[12] MedSegBench: A comprehensive benchmark for medical ... https://pmc.ncbi.nlm.nih.gov/articles/PMC11589128/
[13] [Revue de papier] AMMeBa: A Large-Scale Survey and Dataset of Media-Based Misinformation In-The-Wild https://www.themoonlight.io/fr/review/ammeba-a-large-scale-survey-and-dataset-of-media-based-misinformation-in-the-wild
[14] FairMedFM: Fairness Benchmarking for Medical Imaging ... https://proceedings.neurips.cc/paper_files/paper/2024/file/c9826b9ea5e1b49b256329934a578d83-Paper-Datasets_and_Benchmarks_Track.pdf
[15] A Multimodal Multi-Task Dataset for Benchmarking Health ... https://aclanthology.org/2025.findings-emnlp.1316/
[16] OmniMedVQA: A New Large-Scale Comprehensive Evaluation ... https://arxiv.org/html/2402.09181v2
[17] A Multimodal Multi-Task Dataset for Benchmarking Health ... https://arxiv.org/html/2505.18685v2
[18] MedSegBench: A comprehensive benchmark for medical ... https://www.nature.com/articles/s41597-024-04159-2
[19] DICOM Modalities Explained | Guide to Medical Imaging ... https://collectiveminds.health/articles/dicom-modalities-a-comprehensive-guide-to-medical-imaging-technologies
[20] Combating Biomedical Misinformation through Multi-modal Claim ... https://arxiv.org/abs/2509.13888
[21] Understanding and Using DICOM, the Data Interchange Standard ...pmc.ncbi.nlm.nih.gov › articles › PMC61235 https://pmc.ncbi.nlm.nih.gov/articles/PMC61235/
[22] AVerImaTeC: A Dataset for Automatic Verification of Image-Text Claims with Evidence from the Web https://www.arxiv.org/pdf/2505.17978.pdf
[23] What is DICOM Image Format & Why is It Important in ... https://www.intelerad.com/en/2023/02/23/handling-dicom-medical-imaging-data/
[24] GitHub - kinit-sk/medical-misinformation-dataset https://github.com/kinit-sk/medical-misinformation-dataset
[25] Managing DICOM images: Tips and tricks for the radiologist - PMC https://pmc.ncbi.nlm.nih.gov/articles/PMC3354356/
[26] [Papierüberprüfung] AMMeBa: A Large-Scale Survey and Dataset of Media-Based Misinformation In-The-Wild https://www.themoonlight.io/de/review/ammeba-a-large-scale-survey-and-dataset-of-media-based-misinformation-in-the-wild
[27] Monant Medical Misinformation Dataset: Mapping Articles ... https://zenodo.org/records/5996864
[28] Medical Image File Formats - PMC - NIH https://pmc.ncbi.nlm.nih.gov/articles/PMC3948928/
[29] Doctors warn against dangers of misinformation from AI https://www.ctvnews.ca/health/article/doctors-warn-against-dangers-of-health-misinformation-from-ai-sources/
