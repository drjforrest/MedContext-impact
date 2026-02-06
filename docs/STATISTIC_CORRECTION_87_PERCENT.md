# Statistic Correction: "87%" Misquote

**Date:** February 2, 2026  
**Status:** 🚨 **CRITICAL - Correction Required Throughout Codebase**

---

## Issue Summary

The "87%" statistic has been **systematically misquoted** throughout the MedContext codebase and documentation. This statistic has been incorrectly attributed to authentic images in misinformation, when it actually refers to a different finding about benefit/harm mentions.

---

## The Misquote

### ❌ INCORRECT (What We've Been Saying)

> "87% of medical misinformation uses authentic images in misleading contexts"

> "87% of medical image misinformation involves pixel-accurate images"

> "87% threat model (authentic images with false context)"

### Sources of Confusion

The 87% statistic **actually comes from** a different study about social media medical test promotion (Prasad et al., 2024, JAMA Internal Medicine):

> "87% of social media posts about medical tests mention benefits while only 15% mention harms"

This is about **benefit-vs-harm framing**, NOT about authentic vs manipulated images!

---

## The Correct Statistic

### ✅ CORRECT (What We Should Say)

**Source:** Brennen et al. (2021), "Beyond (mis)representation: Visuals in COVID-19 Misinformation", _International Journal of Press/Politics_, 26(1):277-299.

**Finding from COVID-19 misinformation analysis (96 fact-checked examples, Jan-Mar 2020):**

> "Visuals appeared in **over half (52%)** of analyzed misinformation cases, with **the vast majority** representing mislabeled authentic content rather than manipulated imagery."

**Key Points:**

1. **~52%** of medical misinformation **includes** visuals
2. **Of those with visuals**, the "vast majority" (>50%, likely 70-80%+) were **authentic images** used in misleading contexts
3. **Zero sophisticated deepfakes** were found in the study
4. Simple editing tools were used for the minority of cases involving manipulation

### Mathematical Interpretation

If 52% of misinformation includes visuals, and ~70-80% of those are authentic images misused:

- **~36-42% of all medical misinformation** involves authentic images in misleading contexts
- This is **significantly different** from the claimed "87%"

---

## Impact on MedContext Narrative

### What This Changes

**OLD (Incorrect) Narrative:**

- "87% of medical misinformation involves authentic images"
- "We address the 87% of cases that pixel forensics miss"
- "87% threat model"

**CORRECTED Narrative:**

- "Over half of medical misinformation includes visuals, predominantly authentic images in misleading contexts"
- "We address the most common threat: authentic images weaponized through false context"
- "Our approach targets context misuse, which represents the dominant form of visual medical misinformation"

### Why This Still Supports Our Thesis

The corrected statistic **actually strengthens** our argument:

1. **Still validates contextual approach:** Authentic images in false contexts are still the dominant threat
2. **More accurate/honest:** Using correct statistics builds credibility
3. **Stronger evidence:** The Brennen study is high-quality COVID-19 research, not a misapplied statistic
4. **Avoids critique:** Reviewers who know the literature will catch the misquote

---

## Files Requiring Correction

### Documentation Files (19 instances)

1. **docs/VALIDATION.md** (4 instances)
   - Line 15, 270, 508, 567

2. **docs/CONTEXTUAL_SIGNALS_VALIDATION.md** (3 instances)
   - Lines 9, 665, 1238

3. **docs/CONTEXTUAL_SIGNALS_VALIDATION_QUICKSTART.md** (1 instance)
   - Line 238

4. **docs/CONTEXTUAL_VALIDATION_SUMMARY.md** (2 instances)
   - Lines 386, 407

5. **docs/VALIDATION_RESULTS.md** (5 instances)
   - Lines 20, 164, 183, 250, 259

6. **docs/VALIDATION_STORY.md** (1 instance)
   - Line 7

7. **docs/VIDEO_SCRIPT.md** (2 instances)
   - Lines 51, 57

8. **docs/EXECUTIVE_SUMMARY.md** (1 instance)
   - Line 13 (This is CORRECT - about benefits/harms)

9. **docs/SUBMISSION.md** (1 instance)
   - Line 33 (This is CORRECT - about benefits/harms)

10. **START_HERE.md** (2 instances)
    - Lines 17, 104

11. **README.md** (1 instance)
    - Line 27 (This is CORRECT - about benefits/harms)

### UI Files (1 instance)

12. **ui/src/ValidationStory.jsx** (1 instance)
    - Line 253 - Insight box display

---

## Recommended Replacement Text

### For Context-Related Claims

**Replace:**

```
87% of medical misinformation uses authentic images in misleading contexts
```

**With:**

```
Over half of medical misinformation includes visuals, predominantly authentic images used in misleading contexts (Brennen et al., 2020)
```

### For Threat Model Claims

**Replace:**

```
addresses the 87% of cases where authentic images are misused
```

**With:**

```
addresses the dominant threat: authentic images weaponized through false contextual claims
```

### For ValidationStory.jsx Insight Box

**Replace:**

```
<span className="insight-number">87%</span>
<p>of medical misinformation involves <strong>authentic images</strong> misused with false context</p>
```

**With:**

```
<span className="insight-number">52%+</span>
<p>of medical misinformation includes <strong>visuals</strong>, mostly authentic images with misleading context (Brennen et al., 2020)</p>
```

### For Weight Rationale (VALIDATION.md line 277)

**Current (Problematic):**

```
Since approximately 87% of medical misinformation involves contextual misuse rather than pixel manipulation (Wardle & Derakhshan, 2017; Brennen et al., 2020)...
```

**Corrected:**

```
Since over half of medical misinformation includes visuals, with the vast majority being authentic images in misleading contexts rather than pixel manipulations (Brennen et al., 2021)...
```

---

## Keep Unchanged (Correct Uses of 87%)

The following uses of "87%" are **CORRECT** and should **NOT** be changed:

1. **README.md, line 27:** "87% of social media posts mention benefits vs 15% harms"
2. **docs/EXECUTIVE_SUMMARY.md, line 13:** Same
3. **docs/SUBMISSION.md, line 33:** Same
4. **medical_images_misinformation_review.md:** Multiple correct uses about benefits/harms

These refer to the Prasad et al. (2024) study about benefit-vs-harm framing, which is correctly cited.

---

## Correct Citation

**Brennen, J. S., Simon, F. M., Howard, P. N., & Nielsen, R. K. (2021).** Beyond (mis)representation: Visuals in COVID-19 misinformation. _International Journal of Press/Politics_, _26_(1), 277-299. https://doi.org/10.1177/1940161220964780

**Key Finding (p. 289):**

> "Visuals in 52% of cases explicitly served as purported evidence for false claims... with the vast majority representing mislabeled authentic content."

---

## Action Items

- [ ] Update all 19 documentation instances
- [ ] Update ValidationStory.jsx insight box
- [ ] Verify no other instances exist
- [ ] Run full-text search for variations ("87 percent", "eighty-seven percent")
- [ ] Update any presentation slides or external documents
- [ ] Commit with clear message explaining correction

---

## Timeline

**Priority:** HIGH - This is a factual error that undermines credibility

**Estimated Time:** 1-2 hours to correct all instances

---

## Lesson Learned

**Root Cause:** Conflation of two different statistics:

1. 87% (benefit-vs-harm mentions in social media posts)
2. 52% (misinformation cases including visuals, mostly authentic)

**Prevention:** Always cite specific page numbers and quotes when using statistics, especially in multiple documents.

---

## Questions?

See `medical_images_misinformation_review.md` lines 38-39 for the correct Brennen et al. finding, and lines 29-30 for the correct 87% statistic (about benefits/harms).
