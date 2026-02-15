# Progress Tracker Enhancement - 2D Contextual Authenticity Visualization

## Enhancement Overview

Split the single "Contextual Authenticity" step into **two half-width cards** to visually represent the 2-dimensional nature of contextual authenticity assessment:

1. **Claim Veracity** (Left Half)
2. **Image-Context Alignment** (Right Half)

## Visual Layout

### Before:
```
┌─────────────────────────────────────────────┐
│ Image Integrity                      [status]│
├─────────────────────────────────────────────┤
│ Contextual Authenticity             [status]│  ← Single wide card
├─────────────────────────────────────────────┤
│ Source Verification                  [status]│
├─────────────────────────────────────────────┤
│ Provenance                           [status]│
└─────────────────────────────────────────────┘
```

### After:
```
┌─────────────────────────────────────────────┐
│ Image Integrity                      [status]│
├──────────────────────┬──────────────────────┤
│ Claim Veracity (Core)│ Image-Context    (Core)
│ MedGemma assesses    │ Alignment        │
│ factual accuracy     │ MedGemma evaluates│
│                      │ image-claim fit  │
│           [⏳ status]│         [⏳ status]│
├──────────────────────┴──────────────────────┤
│ Source Verification                  [status]│
├─────────────────────────────────────────────┤
│ Provenance                           [status]│
└─────────────────────────────────────────────┘
```

## Implementation Details

### 1. Updated Agent Steps Configuration

**New Structure:**
```javascript
const agentSteps = [
  {
    key: 'image_integrity',
    label: 'Image Integrity',
    detail: 'Pixel forensics, metadata, and manipulation detection.',
    toolKey: 'forensics',
    isCore: false,
  },
  {
    key: 'claim_veracity',
    label: 'Claim Veracity',
    detail: 'MedGemma assesses factual accuracy of the claim.',
    toolKey: null,
    isCore: true,
    isHalfWidth: true,  // ← New flag
  },
  {
    key: 'context_alignment',
    label: 'Image-Context Alignment',
    detail: 'MedGemma evaluates how well image supports the claim.',
    toolKey: null,
    isCore: true,
    isHalfWidth: true,  // ← New flag
  },
  // ... other steps
]
```

### 2. CSS Grid Layout

**Grid Configuration:**
```css
.activity-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.activity-step.activity-half {
  grid-column: span 1;  /* Half-width */
}

.activity-step:not(.activity-half) {
  grid-column: span 2;  /* Full-width */
}
```

### 3. Visual Treatment

**Both Core Modules:**
- Marked with "(Core)" label
- Always show "active" state during loading
- Animate with blue pulse when running
- Show "✓ Complete" when done

**Side-by-Side Display:**
- Each takes 50% width on desktop
- Stack vertically on mobile (responsive grid)
- Equal height for visual balance
- Subtle background tint groups them together

### 4. Updated Helper Text

**During Loading:**
```
"Running 2-dimensional contextual authenticity: 
Claim Veracity + Image-Context Alignment. 
Add-on modules shown if selected."
```

**After Completion:**
```
"Workflow complete: core contextual signals 
(veracity + alignment) plus agent-selected add-ons."
```

## Benefits

### 1. **Reinforces Core Thesis**
The side-by-side layout visually demonstrates that contextual authenticity requires **BOTH dimensions together**:
- Veracity alone ❌ (50.9%)
- Alignment alone ❌ (76.1%)
- Both together ✅ (94.5%)

### 2. **Educational Value**
Users immediately understand:
- These are the TWO core signals
- They work in parallel
- Both are always analyzed (marked "Core")
- They combine to detect contextual misinformation

### 3. **Progress Clarity**
Users can now see:
- ⏳ Claim Veracity: Analyzing...
- ⏳ Image-Context Alignment: Analyzing...

Instead of generic:
- ⏳ Contextual Authenticity: Analyzing...

### 4. **Aligns with Results Section**
The progress tracker now matches the results presentation:
- Results show separate veracity + alignment scores
- Progress tracker shows separate veracity + alignment steps
- Consistent mental model throughout UI

## Responsive Behavior

**Desktop (≥768px):**
```
┌──────────────┬──────────────┐
│  Veracity    │  Alignment   │
│   (Core)     │   (Core)     │
└──────────────┴──────────────┘
```

**Mobile (<768px):**
```
┌──────────────┐
│  Veracity    │
│   (Core)     │
├──────────────┤
│  Alignment   │
│   (Core)     │
└──────────────┘
```

## Visual States During Workflow

### State 1: Loading (Both Active)
```
┌──────────────────────┬──────────────────────┐
│ Claim Veracity (Core)│ Image-Context    (Core)
│ ⏳ Analyzing...      │ Alignment        │
│ [pulsing blue]       │ ⏳ Analyzing...  │
│                      │ [pulsing blue]   │
└──────────────────────┴──────────────────────┘
```

### State 2: Complete (Both Done)
```
┌──────────────────────┬──────────────────────┐
│ Claim Veracity (Core)│ Image-Context    (Core)
│ ✓ Complete           │ Alignment        │
│ [green background]   │ ✓ Complete       │
│                      │ [green background]│
└──────────────────────┴──────────────────────┘
```

## Comparison to Original Design

### What Changed:
- **From:** 1 wide "Contextual Authenticity" card
- **To:** 2 half-width cards (Veracity + Alignment)

### What Stayed Same:
- Core always runs (both marked "Core")
- Add-ons conditional (same as before)
- State logic (active/done/skipped)
- Animations and styling

### Why Better:
✅ **More accurate representation** — Shows 2D nature  
✅ **Educational** — Users learn about both dimensions  
✅ **Consistent with results** — Matches score display  
✅ **Visual hierarchy** — Core pair stands out  
✅ **Progress detail** — Can see both analyses happening  

## Technical Implementation

### Grid Behavior:
- Row 1: Image Integrity (full width)
- Row 2 Col 1: Claim Veracity (half width)
- Row 2 Col 2: Image-Context Alignment (half width)
- Row 3: Source Verification (full width)
- Row 4: Provenance (full width)

### State Management:
```javascript
// Both veracity and alignment use same logic
if (step.isCore) {
  if (status === 'loading') return 'active'
  return status === 'success' ? 'done' : 'idle'
}
```

### CSS Classes Applied:
- `.activity-step` — Base card styling
- `.activity-half` — Half-width grid span
- `.activity-active` — Blue pulse animation
- `.activity-done` — Green success state

## User Testing Scenarios

**Scenario 1: User sees loading**
- Both veracity and alignment pulse blue simultaneously
- Clear indication that TWO analyses are running
- Helper text mentions "2-dimensional"

**Scenario 2: User sees completed**
- Both show green ✓ Complete
- Visual confirmation that BOTH dimensions succeeded
- Results section below shows scores for each

**Scenario 3: Mobile user**
- Cards stack vertically but remain distinct
- Same information, responsive layout
- Touch targets remain accessible

## Summary

The progress tracker now **visually embodies the core thesis**: contextual authenticity is inherently 2-dimensional (Veracity + Alignment), and both dimensions are **always analyzed in parallel** as core features of the system.

This creates a consistent narrative from:
1. **Progress tracker** → Shows 2 core dimensions running
2. **Results display** → Shows 2 core scores
3. **Validation story** → Proves 2 dimensions required
4. **Documentation** → Explains 2-dimensional framework

Result: **Users understand the 2D nature of contextual authenticity at a glance!** 🎯
