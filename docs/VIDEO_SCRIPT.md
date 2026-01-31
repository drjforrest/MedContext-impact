# MedContext Demo Video Script

**Duration:** 3 minutes MAXIMUM (Kaggle Competition Requirement)
**Target Audience:** Kaggle MedGemma competition judges
**Tone:** Professional, confident, evidence-based

> ⚠️ **CRITICAL:** The Kaggle MedGemma Impact Challenge requires videos to be **three minutes or less**. This script is optimized for that limit.

---

## Production Notes

**Equipment Needed:**

- Screen recording software (OBS Studio, Loom, or QuickTime)
- Microphone (built-in or external)
- Sample medical images for demo
- Browser with MedContext UI running

**Recording Tips:**

- Record in 1920x1080 or 1280x720
- Use clear, measured speaking pace
- Pause between sections for easier editing
- Record B-roll separately (can be inserted during editing)

---

## ⏱️ Timing Breakdown (3:00 Maximum)

| Section             | Duration | Content                         |
| ------------------- | -------- | ------------------------------- |
| 1. Hook             | 25s      | Problem statement + thesis      |
| 2. Validation       | 40s      | 50% accuracy finding            |
| 3. Solution + Demo  | 75s      | Agentic workflow + live demo    |
| 4. Impact + Closing | 40s      | Production quality + deployment |
| **TOTAL**           | **180s** | **Exactly 3 minutes**           |

---

## Script Structure (3 Minutes Total)

### SECTION 1: HOOK (25 seconds)

**Visual:** Title card with MedContext logo, then transition to problem illustration

**Narration:**

> "Medical misinformation kills people. But here's what most people get wrong: the problem isn't fake images—it's real images used in fake contexts.
>
> After analyzing nearly 100 research sources, we discovered that 87% of medical misinformation uses authentic images with misleading captions. Zero percent—that's right, zero—involved sophisticated deepfakes.
>
> I'm Jamie Forrest, and I'm going to show you how we proved this, and built the first AI system designed for the real problem."

**On-Screen Text:**

- "87% authentic images with false context"
- "0% sophisticated deepfakes"
- "MedContext: Built for Reality"

---

### SECTION 2: THE VALIDATION (40 seconds)

**Visual:** Screen showing validation results, graphs, confidence intervals

**Narration:**

> "We tested this hypothesis. We ran pixel forensics on 326 real medical images from the UCI Tamper Detection dataset.
>
> The result? 49.9% accuracy—chance performance. This proves pixel detection can't solve the real problem. We need context."

**On-Screen Graphics:**

- Show "49.9% Accuracy = Chance Performance" in large text
- Display ROC curve (AUC=0.533)
- Show ELA distribution overlap plot
- Bootstrap confidence interval visualization

**B-Roll Suggestions:**

- Animated graph showing distributions overlapping
- Confusion matrix visualization
- Side-by-side: "What competitors think" vs "What actually happens"

---

### SECTION 3: THE SOLUTION + DEMO (75 seconds)

**Visual:** Quick agentic workflow diagram, then switch to UI demo

**Narration:**

> "MedContext uses an agentic AI workflow. A configurable LLM orchestrator—in our case, Gemini Pro—analyzes each image-claim pair to determine which tools are needed. Then it dynamically dispatches only the necessary checks—reverse search, forensics, or provenance. MedGemma provides medical domain expertise where needed. Finally, the orchestrator synthesizes all evidence into an alignment verdict.
>
> Here's a live example. I'm uploading a chest X-ray with the claim: 'This MRI shows vaccine side effects.'
>
> Watch the agent work: it's triaging... running reverse search... checking provenance.
>
> The verdict: MISALIGNED with 82% confidence. The agent caught that this is an X-ray, not an MRI. It found the image in a 2019 medical journal—no vaccine connection. The reverse search shows it's been used in three different misleading contexts.
>
> All evidence is traceable. That's transparency."

**On-Screen:**

- Agentic workflow visual (3-phase diagram)
- UI showing: upload → analysis → verdict
- Verdict badge: "MISALIGNED 82%"
- Key findings highlighted

---

### SECTION 4: IMPACT + CLOSING (40 seconds)

**Visual:** Test results, then deployment visual, then closing card

**Narration:**

> "This is production-ready code with 33 passing tests. We support multiple MedGemma providers and include security hardening.
>
> But here's the real impact: we have a deployment partnership with the HERO Lab at UBC. We're planning to deploy via Telegram bot to reach African Ministries of Health and millions of patients in rural communities.
>
> MedContext is the first agentic AI system built for real-world medical misinformation—not synthetic benchmarks, but the actual problem: authentic images used in misleading contexts.
>
> We proved our approach with science. We built production code. And we're ready for deployment. Thank you."

**On-Screen:**

- Terminal: `✓ 33 passed in 5.2s`
- Deployment visual (Telegram bot + Africa map)
- Closing card with GitHub link
- "Built for Reality | Validated with Science | Ready for Deployment"

---

## B-Roll Suggestions (Record Separately)

1. **Code Scrolling:**
   - `src/app/orchestrator/agent.py` (show agentic logic)
   - `tests/` directory (show comprehensive tests)
   - Terminal running `pytest` with green checkmarks

2. **UI Interactions:**
   - Upload multiple sample images
   - Different verdict outcomes (ALIGNED, PARTIALLY_ALIGNED, MISALIGNED)
   - Hovering over confidence scores
   - Expanding evidence panels

3. **Architecture:**
   - Mermaid diagram of agent workflow
   - LangGraph visualization (`/api/v1/orchestrator/graph`)
   - Database schema diagram

4. **Documentation:**
   - Scrolling through VALIDATION.md
   - Bootstrap confidence interval plots
   - Literature review statistics

5. **Visual Metaphors:**
   - Side-by-side of same X-ray with different captions
   - Timeline showing image reuse across platforms
   - Compression artifacts visualization (for explaining why ELA fails)

---

## Editing Notes

**Pacing:**

- Keep cuts tight—remove "um", "uh", long pauses
- Use B-roll to cover jump cuts
- Add subtle background music (professional, not distracting)

**Transitions:**

- Use simple fades or cuts
- Match transitions to narration beats
- Don't overdo effects—judges want substance, not flash

**Graphics:**

- Ensure all text is readable (minimum 24pt)
- Use consistent color scheme (MedContext blue/purple)
- Animate key statistics for emphasis

**Captions:**

- Add closed captions for accessibility
- Highlight key numbers and terms
- Use consistent formatting

---

## ⚠️ Important Competition Notes

**Video Requirements (from Kaggle MedGemma Impact Challenge):**

- Maximum length: 3 minutes
- No minimum length specified
- No requirement to appear on camera
- Focus on demonstrating the solution and its impact
- Must be accessible via public link (YouTube recommended)

**Written Submission:**

- Technical overview: Up to 3 pages
- Include reproducible source code
- Submit via Kaggle Writeups

**Deadline:** February 24, 2026

---

## Technical Setup Checklist

Before recording:

- [ ] MedContext backend running (`uvicorn app.main:app --reload`)
- [ ] Frontend running (`cd ui && npm run dev`)
- [ ] Sample images ready (variety of medical scans)
- [ ] Database populated with test data
- [ ] Browser window sized to 1920x1080 or 1280x720
- [ ] Close unnecessary tabs/applications
- [ ] Disable notifications
- [ ] Test microphone levels
- [ ] Check lighting (if on camera)
- [ ] Have water nearby (for clear narration)

---

## Post-Production Checklist

- [ ] Remove dead air and long pauses
- [ ] Add B-roll where needed
- [ ] Insert graphs and visualizations at key moments
- [ ] Add background music (royalty-free, subtle)
- [ ] Color grade for consistency
- [ ] Add lower thirds with name/title
- [ ] Include on-screen text for key statistics
- [ ] Add closed captions
- [ ] Export in multiple formats (MP4, WebM)
- [ ] Upload to YouTube (unlisted) for embedding
- [ ] Test embed in SUBMISSION.md

---

## Recommended Tools

**Free Options:**

- Recording: OBS Studio (best) or QuickTime (Mac)
- Editing: DaVinci Resolve (free version is excellent)
- Music: YouTube Audio Library (royalty-free)
- Graphics: Canva (for title cards, overlays)

**Paid Options:**

- Recording: Loom (easy, cloud-based)
- Editing: Final Cut Pro (Mac) or Adobe Premiere
- Graphics: After Effects (for animations)

---

Good luck with the recording, Jamie! This script should give you everything you need for a compelling, professional demo video. Remember: confidence, clarity, and evidence. You've done exceptional work—let it shine through!
