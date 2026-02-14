# MedContext Demo Video Script
**Target Duration**: 3 minutes maximum (~450 words at 150 wpm)

---

## OPENING: The Problem (0:00-0:30)

**[VISUAL: Show examples of medical misinformation on social media]**

Medical misinformation spreads rapidly online, but detecting it is uniquely challenging. Unlike deepfakes or manipulated images, most medical misinformation uses **authentic images with misleading claims**.

Traditional pixel-based forensics can't catch this. A real CT scan paired with a false diagnosis. An authentic graph with misinterpreted data. The image is real—but the story is fake.

**[TRANSITION: Show title card "MedContext"]**

---

## THE SOLUTION: MedContext (0:30-1:00)

**[VISUAL: Show system architecture diagram]**

MedContext solves this with **three-dimensional authenticity analysis**:

1. **Image Integrity** - Pixel-level forensics for tampering detection
2. **Claim Veracity** - Medical fact-checking powered by MedGemma
3. **Context Alignment** - Does the claim match what the image actually shows?

**Why three dimensions?**

Because medical misinformation is multi-faceted. A manipulated scan is different from a real scan with a false diagnosis, which is different from an authentic image used in the wrong context. Each dimension catches what the others miss.

---

## KEY FEATURES (1:00-1:15)

**[VISUAL: Show UI features]**

MedContext provides:
- **Blockchain provenance** - Immutable audit trail on Polygon
- **Multi-modal analysis** - Images, DICOM files, claims, and metadata
- **Explainable results** - Clear rationale for every decision
- **Mobile-ready** - Telegram bot for instant verification

---

## DEMO: Example 1 - Misinformation Detected (1:15-2:00)

**[VISUAL: Screen recording - Upload COVID graph image]**

Let's see it in action. First, a COVID-19 positivity rate graph from Johns Hopkins. The claim states: "herd immunity has been reached."

**[Show analysis running]**

MedContext activates multiple modules:
- Contextual analysis via MedGemma
- Reverse image search
- Provenance chain creation

**[Show results - Three-dimensional scores]**

Results:
- 🟢 **Image Integrity**: AUTHENTIC - It's a real Johns Hopkins graph
- 🔴 **Claim Veracity**: INACCURATE - Epidemiological evidence contradicts the claim
- 🔴 **Context Alignment**: MISALIGNED - The graph doesn't support the "herd immunity" interpretation

**Verdict**: ⚠️ **Misinformation Detected**

The image is authentic, but the interpretation is false—exactly the kind of contextual misinformation that pixel forensics misses.

---

## DEMO: Example 2 - Legitimate Content (2:00-2:30)

**[VISUAL: Screen recording - Upload NIH brain research image]**

Second example: An NIH brain research image with a claim about Alzheimer's therapy.

**[Show analysis and results]**

Results:
- 🟢 **Image Integrity**: AUTHENTIC
- 🟢 **Claim Veracity**: ACCURATE - Matches published NIH research
- 🟢 **Context Alignment**: ALIGNED - Image matches the described study

**Verdict**: ✅ **No Misinformation Detected**

MedContext correctly validates legitimate medical research, avoiding false positives.

---

## VALIDATION RESULTS (2:30-2:50)

**[VISUAL: Show validation charts - confusion matrix, ROC curve, performance comparison]**

We validated MedContext on 163 Med-MMHL test cases against expert-informed ground truth:
- **96.3% accuracy**
- **98.1% precision and recall**

**[VISUAL: Show performance comparison chart]**

The key finding: **No single dimension is sufficient**.
- Image Integrity alone: **65% accuracy**
- Claim Veracity alone: **72% accuracy**
- Context Alignment alone: **71% accuracy**
- **All three combined: 96.3% accuracy**

You need all three dimensions to reliably detect medical misinformation.

---

## CLOSING (2:50-3:00)

**[VISUAL: Show GitHub repo, documentation links]**

MedContext demonstrates that **context is crucial** for medical misinformation detection. When pixels tell the truth but words tell lies, we need systems that understand both.

**Open source. Blockchain-anchored. Empirically validated.**

Thank you.

**[END SCREEN: Project links, QR code to demo]**

---

## PRODUCTION NOTES

### Timing Breakdown
- Opening: 30 seconds
- Solution & Justification: 30 seconds
- Key Features: 15 seconds
- Demo Example 1: 45 seconds
- Demo Example 2: 30 seconds
- Validation: 20 seconds
- Closing: 10 seconds
- **Total: 3:00**

### Visual Requirements
1. Social media misinformation examples (blur sensitive content)
2. System architecture diagram
3. PoJ validation results table/chart
4. UI screen recordings (2 full analysis walkthroughs)
5. Validation charts:
   - Confusion matrix
   - ROC curve
   - Performance comparison bar chart
6. End screen with links

### Screen Recording Notes

**Example 1 - Misinformation**:
- Show image upload of `example1_misinformation_covid_graph.jpg`
- Copy claim from `demo_examples_metadata.json`
- Record full analysis (modules → scores → rationale → verdict)
- Highlight the contrast: green Image Integrity, red Claim/Alignment

**Example 2 - Legitimate**:
- Show image upload of `example2_legitimate_brain_research.jpg`
- Copy claim from `demo_examples_metadata.json`
- Record full analysis
- Show all three dimensions green

### Voice-Over Tips
- Maintain steady pace (150 wpm)
- Emphasize key numbers: 50% vs 97.5%, 96.3% accuracy, 98.1% precision
- Pause briefly at transitions
- Stress the key insight: "Most medical misinformation doesn't manipulate pixels—it manipulates *meaning*"

### Optional B-Roll
- Medical professionals reviewing information on devices
- Social media feeds with health content
- Blockchain transaction visualization
- Code snippets (if showing technical depth)

---

## ALTERNATE 2-MINUTE VERSION

If time is tighter, cut:
- Key Features section (15s) - show briefly in demos instead
- Demo Example 2 (30s) - focus only on misinformation detection
- Extend validation section with saved time

This maintains core narrative: Problem → Solution → Proof → Validation
