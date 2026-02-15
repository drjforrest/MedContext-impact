# Threshold Configuration Feature - Implementation Summary

## Overview

Extended the MedContext system to support **configurable decision thresholds** in the main verification workflow. Users can now adjust veracity and alignment thresholds and choose decision logic (OR/AND/MIN) directly in the UI, allowing them to apply optimized thresholds discovered via the Threshold Optimization tab.

## Changes Made

### 1. Frontend UI (`ui/src/App.jsx`)

**New State Variables:**
```javascript
const [veracityThreshold, setVeracityThreshold] = useState(0.65)
const [alignmentThreshold, setAlignmentThreshold] = useState(0.30)
const [decisionLogic, setDecisionLogic] = useState('OR')
const [showAdvanced, setShowAdvanced] = useState(false)
```

**New UI Section:**
- Added collapsible "Decision Thresholds" section with "Show Advanced" toggle
- **Veracity Threshold Control:** Range slider (0-1) + number input
- **Alignment Threshold Control:** Range slider (0-1) + number input  
- **Decision Logic Selector:** Dropdown with OR/AND/MIN options and descriptions
- **Real-time Feedback:** Shows current configuration in helper text
- **Tip Box:** Links to Threshold Optimization tab for finding optimal values

**Form Submission:**
- Thresholds and logic appended to FormData sent to `/api/v1/orchestrator/run`

### 2. Backend API (`src/app/api/v1/endpoints/orchestrator.py`)

**Updated Endpoint Signature:**
```python
@router.post("/run")
async def run_agent(
    ...
    veracity_threshold: float = Form(default=0.65),
    alignment_threshold: float = Form(default=0.30),
    decision_logic: str = Form(default="OR"),
    ...
)
```

**Parameters passed through:**
- `orchestrator.py` → `ingestion.py::ingest_and_run_agentic()` → `langgraph_agent.py::run()`

### 3. Ingestion Layer (`src/app/api/v1/endpoints/ingestion.py`)

**Updated Function Signature:**
```python
def ingest_and_run_agentic(
    ...
    veracity_threshold: float = 0.65,
    alignment_threshold: float = 0.30,
    decision_logic: str = "OR",
) -> AgentRunResponse:
```

**Passes parameters to agent:**
```python
result = agent.run(
    ...
    veracity_threshold=veracity_threshold,
    alignment_threshold=alignment_threshold,
    decision_logic=decision_logic,
)
```

### 4. Agent Layer (`src/app/orchestrator/langgraph_agent.py`)

**Updated AgentState TypedDict:**
```python
class AgentState(TypedDict, total=False):
    ...
    # Threshold configuration
    veracity_threshold: float
    alignment_threshold: float
    decision_logic: str
```

**Updated `run()` and `run_with_trace()` Methods:**
- Accept threshold parameters with defaults
- Add to initial state dict

**Updated `_build_contextual_integrity()` Method:**
- Extracts thresholds from state: `state.get("veracity_threshold", 0.65)`
- Applies configurable decision logic:
  - **OR:** `veracity < threshold OR alignment < threshold` (high recall)
  - **AND:** `veracity < threshold AND alignment < threshold` (high precision)
  - **MIN:** `min(veracity, alignment) < min_threshold` (balanced)
- Determines `is_misinformation` boolean based on chosen logic
- Returns threshold config and decision in response:
  ```python
  {
      "is_misinformation": bool,
      "decision_logic": str,
      "thresholds": {
          "veracity": float,
          "alignment": float,
      },
      ...
  }
  ```

## Decision Logic Implementations

### OR Logic (Default, High Recall)
```python
is_misinformation = (veracity_value < veracity_threshold) or (alignment_value < alignment_threshold)
```
**Use Case:** Health misinformation detection where missing a dangerous case is costly

### AND Logic (High Precision)
```python
is_misinformation = (veracity_value < veracity_threshold) and (alignment_value < alignment_threshold)
```
**Use Case:** Applications where false positives are more costly than misses

### MIN Logic (Balanced)
```python
min_score = min(veracity_value, alignment_value)
min_threshold = min(veracity_threshold, alignment_threshold)
is_misinformation = min_score < min_threshold
```
**Use Case:** Balanced risk tolerance between FP and FN

## User Workflow

1. User opens "Verify Image" tab
2. Uploads image and enters claim as usual
3. Clicks "Show Advanced" under "Decision Thresholds"
4. Adjusts sliders or enters values for veracity and alignment thresholds
5. Selects decision logic (OR/AND/MIN) from dropdown
6. Runs verification with custom thresholds
7. Results include `is_misinformation` flag and show which thresholds/logic were used

## Default Values

Based on Med-MMHL validation results (MedGemma 27B):
- **Veracity Threshold:** 0.65
- **Alignment Threshold:** 0.30
- **Decision Logic:** OR
- **Performance:** 94.5% accuracy [95% CI: 90.8%, 97.5%]

## Integration with Threshold Optimization

The "Threshold Optimization" tab finds optimal thresholds for user's specific domain. Users can then:
1. Run optimization on their validation dataset
2. Copy optimal threshold values from results
3. Paste into "Decision Thresholds" section in "Verify Image" tab
4. Run verification with optimized configuration

## Benefits

✅ **Flexible:** Users can adapt system to their domain and risk tolerance  
✅ **Data-Driven:** Thresholds optimized via grid search + bootstrap CI  
✅ **Transparent:** UI shows exactly which thresholds are being used  
✅ **Persistent:** Settings remembered during session (not across reloads)  
✅ **Backward Compatible:** Defaults maintain existing behavior  

## API Response Schema Extension

The `contextual_integrity` object in API responses now includes:

```json
{
  "contextual_integrity": {
    "score": 0.92,
    "is_misinformation": false,
    "decision_logic": "OR",
    "thresholds": {
      "veracity": 0.65,
      "alignment": 0.30
    },
    "claim_veracity": {...},
    "signals": {...},
    ...
  }
}
```

## Future Enhancements

- Persist threshold preferences in localStorage
- Add preset configurations (e.g., "High Recall", "High Precision", "Balanced")
- Show predicted precision/recall based on validation results
- Add threshold impact visualization (what-if scenarios)
- Support per-module confidence threshold tuning

## Testing Notes

**Manual Testing:**
1. Test with default thresholds (0.65/0.30/OR) → should match previous behavior
2. Test with extreme thresholds (0.0/1.0) → verify all flagged/none flagged
3. Test all three decision logics → verify correct behavior
4. Test threshold adjustments via sliders and number inputs
5. Verify threshold values appear in API response

**Integration Testing:**
- Ensure thresholds flow through: UI → API → Ingestion → Agent → Decision
- Verify `is_misinformation` flag correctly reflects threshold application
- Confirm response includes threshold configuration for audit trail
