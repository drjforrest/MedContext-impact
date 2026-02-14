# Demo Video Examples

This directory contains 2 carefully selected image-claim pairs from the Med-MMHL validation dataset that best represent the MedContext project's capabilities.

## Examples Overview

### Example 1: Misinformation Detection
**File**: `example1_misinformation_covid_graph.jpg`
- **Type**: Misinformation (Misaligned Claim)
- **Image**: COVID-19 positivity rate graph from Johns Hopkins University
- **Claim**: Misleading interpretation claiming "herd immunity has been reached" based on graph trends
- **Ground Truth**:
  - Image Integrity: Authentic (pixel-level)
  - Claim Alignment: Misaligned
  - Plausibility: Low
  - **Result**: ⚠️ Misinformation Detected

**Why this example is representative**:
- Demonstrates detection of **contextual misinformation** (real image + false interpretation)
- Shows how MedContext evaluates **claim veracity** separate from image authenticity
- Illustrates the **three-dimensional analysis**: Image Integrity (✅), Claim Veracity (❌), Context Alignment (❌)
- Classic example of how authentic medical/scientific data can be misrepresented

---

### Example 2: Legitimate Content
**File**: `example2_legitimate_brain_research.jpg`
- **Type**: Legitimate (Aligned Claim)
- **Image**: Brain lymphatic system research illustration from NIH
- **Claim**: Accurate description of NIH-funded study on brain's waste removal system and Alzheimer's therapy
- **Ground Truth**:
  - Image Integrity: Authentic
  - Claim Alignment: Aligned
  - Plausibility: High
  - **Result**: ✅ No Misinformation Detected

**Why this example is representative**:
- Demonstrates **accurate detection of legitimate medical content**
- Shows system's ability to verify factually correct claims
- Illustrates proper **context alignment** between image and claim
- Represents typical legitimate medical research communication

---

## Why These Two Examples?

These examples were chosen because they:

1. **Show Contrast**: One misinformation case vs. one legitimate case
2. **Demonstrate Core Capabilities**:
   - Three-dimensional authenticity analysis (Image Integrity, Claim Veracity, Context Alignment)
   - Contextual misinformation detection (not just pixel manipulation)
   - Medical domain expertise (COVID-19 epidemiology, neuroscience research)
3. **Real-World Relevance**: Both represent actual misinformation/information patterns encountered in medical social media
4. **Clear Ground Truth**: Unambiguous labels make them ideal for demonstration
5. **Visual Appeal**: Both images are clear and understandable for video presentation

## Dataset Statistics

- **Source**: Med-MMHL validation dataset
- **Total Validation Samples**: 163
- **Overall System Accuracy**: 96.3%
- **Precision**: 98.1%
- **Recall**: 98.1%

## Usage for Demo Video

These examples can be used to:
1. Walk through the MedContext analysis pipeline step-by-step
2. Show the UI/Telegram bot in action
3. Demonstrate the three-dimensional scoring system
4. Explain how contextual signals complement pixel forensics
5. Highlight the importance of source verification and claim validation

## File Structure

```
demo_video/
├── README.md                                    # This file
├── example1_misinformation_covid_graph.jpg      # Misinformation example
├── example2_legitimate_brain_research.jpg       # Legitimate example
└── demo_examples_metadata.json                  # Full claims and ground truth
```

## Video Production Files

This directory includes everything needed for video production:

- **[VIDEO_SCRIPT.md](VIDEO_SCRIPT.md)** - Complete 3-minute narration script with timing
- **[TALKING_POINTS.md](TALKING_POINTS.md)** - Key statistics, soundbites, and technical details
- **[SHOT_LIST.md](SHOT_LIST.md)** - Detailed storyboard with 17 shots and visual requirements
- **demo_examples_metadata.json** - Full claims and ground truth for both examples
- **example1_misinformation_covid_graph.jpg** - COVID graph misinformation example
- **example2_legitimate_brain_research.jpg** - NIH research legitimate example

## Next Steps

To produce the demo video:
1. Review [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md) for complete narration (3 minutes)
2. Check [SHOT_LIST.md](SHOT_LIST.md) for visual requirements (17 shots)
3. Screen record both examples using the UI:
   - Load images into MedContext
   - Paste claims from `demo_examples_metadata.json`
   - Show full analysis (modules → scores → rationale → verdict)
4. Export validation charts from `ui/public/validation/`
5. Follow timing breakdown in script (0:00-3:00)
6. Add end screen with project links
