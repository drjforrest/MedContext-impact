graph TB
Start([User uploads image + claim]) --> TriageStart{TRIAGE PHASE}

    TriageStart --> MedGemma[🩺 MedGemma<br/>Medical Analysis]

    MedGemma --> MedOutput["Medical Assessment:<br/>• Image type (X-ray, MRI, CT)<br/>• Anatomical findings<br/>• Medical plausibility<br/>• Claim assessment<br/>• Medical caveats"]

    MedOutput --> Orchestrator[🧠 Gemini Pro<br/>Tool Selection]

    Orchestrator --> ToolDecision["Strategic Decision:<br/>• Which tools needed?<br/>• reverse_search?<br/>• forensics?<br/>• provenance?<br/>• Reasoning"]

    ToolDecision --> DispatchStart{TOOL DISPATCH PHASE}

    DispatchStart --> CheckReverse{reverse_search<br/>selected?}
    DispatchStart --> CheckForensics{forensics<br/>selected?}
    DispatchStart --> CheckProvenance{provenance<br/>selected?}

    CheckReverse -->|Yes| ReverseSearch[🔍 Reverse Search<br/>Check prior uses]
    CheckReverse -->|No| SkipReverse[ ]

    CheckForensics -->|Yes| Forensics[🔬 Forensics<br/>Pixel analysis + EXIF]
    CheckForensics -->|No| SkipForensics[ ]

    CheckProvenance -->|Yes| Provenance[⛓️ Provenance<br/>Blockchain verification]
    CheckProvenance -->|No| SkipProvenance[ ]

    ReverseSearch --> Evidence[📊 Evidence Collection]
    Forensics --> Evidence
    Provenance --> Evidence
    SkipReverse -.-> Evidence
    SkipForensics -.-> Evidence
    SkipProvenance -.-> Evidence

    Evidence --> SynthesisStart{SYNTHESIS PHASE}

    SynthesisStart --> Synthesizer[🧠 Gemini Pro<br/>Evidence Aggregation]

    Synthesizer --> SynthInput["Inputs:<br/>• MedGemma's medical analysis<br/>• Tool selection reasoning<br/>• Reverse search results<br/>• Forensics findings<br/>• Provenance chain<br/>• User claim"]

    SynthInput --> FinalVerdict["✅ Final Verdict:<br/>• Alignment (aligned/misaligned/unclear)<br/>• Confidence score<br/>• Rationale<br/>• Context quote<br/>• Risk assessment"]

    FinalVerdict --> End([Return to user])

    style MedGemma fill:#e1f5ff,stroke:#0066cc,stroke-width:3px
    style Orchestrator fill:#fff4e1,stroke:#ff9800,stroke-width:3px
    style Synthesizer fill:#fff4e1,stroke:#ff9800,stroke-width:3px
    style MedOutput fill:#e8f5e9,stroke:#4caf50
    style ToolDecision fill:#fff9c4,stroke:#fbc02d
    style FinalVerdict fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    style TriageStart fill:#ffebee,stroke:#c62828
    style DispatchStart fill:#ffebee,stroke:#c62828
    style SynthesisStart fill:#ffebee,stroke:#c62828

    classDef toolStyle fill:#e3f2fd,stroke:#1976d2
    class ReverseSearch,Forensics,Provenance toolStyle

```

## Key Architecture Points:

### 🩺 **MedGemma's Role (Medical Expert):**
- Analyzes medical images
- Assesses claim plausibility
- Provides medical context
- **Does NOT decide tools**

### 🧠 **Gemini Pro's Role (Orchestrator):**
- **Triage:** Decides which investigative tools to deploy (based on MedGemma's analysis)
- **Synthesis:** Aggregates all evidence into final verdict
- **NOT a medical expert** - defers to MedGemma for medical questions

### 🔧 **Tool Dispatch:**
- Only runs tools selected by orchestrator
- Dynamic, not always all three
- Each tool provides specific evidence

### 📊 **Evidence Flow:**
```

MedGemma (medical) → Orchestrator (strategy) → Tools (investigation) → Orchestrator (synthesis) → Verdict
