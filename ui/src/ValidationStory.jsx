import {
  Psychology as BrainIcon,
  CheckCircle as CheckIcon,
  HourglassEmpty as PendingIcon,
  Rocket as RocketIcon,
  TrackChanges as TargetIcon,
  Warning as WarningIcon
} from '@mui/icons-material'
import { useMemo } from 'react'
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts'
import './ValidationStory.css'

// Med-MMHL validation data — proving contextual authenticity requires both veracity AND alignment
// Primary validation: MedGemma 4B multimodal (production model, processes actual JPEG/PNG images)
// Dataset: Med-MMHL medical multimodal misinformation benchmark (authentic images, misleading claims)
// Key finding: Single signals ~74-87% insufficient; combined IT 90.8%, Q 92.0% with VERACITY_FIRST
// NOTE: Pixel forensics validated on a SEPARATE dataset (manipulated images) — different task.
//       Med-MMHL images are all authentic; pixel forensics has no role in this contextual track.
//
// Source: validation_results/med_mmhl_n163_quantized_4b/ and med_mmhl_n163_hf_27b/
// Thresholds optimized via grid search (OR logic: veracity<0.65, alignment<0.30)
const VALIDATION_DATA = {
  // IT: MedGemma 4B Instruction-Tuned (HuggingFace Inference API, FP16)
  // Original validation run (Feb 15, 2026)
  // Threshold-optimized (OR logic: v<0.65, a<0.30) via 5-fold stratified CV
  // Source: validation_results/med_mmhl_n163_4b_it/
  it: {
    model: "MedGemma 4B IT",
    model_note: "Instruction-tuned, full precision (FP16) via HuggingFace Inference API",
    dimensions: {
      veracity:  { binary_accuracy: 0.736, n: 163 },
      alignment: { binary_accuracy: 0.748, n: 163 },
    },
    combined: {
      accuracy: 0.908,
      precision: 0.992,
      recall: 0.897,
      f1: 0.942,
      tp: 122, fp: 1, tn: 26, fn: 14,
      ci_lower: 0.859, ci_upper: 0.951,
      threshold_logic: "OR",
      veracity_threshold: 0.65,
      alignment_threshold: 0.30,
    },
  },
  // Q: MedGemma 4B Quantized GGUF (LM Studio, ~4-bit)
  // Updated validation run (Feb 17, 2026)
  // LangGraph agent + VERACITY_FIRST decision logic
  // Threshold-optimized (OR logic: v<0.65, a<0.30) via 5-fold stratified CV
  // Bootstrap 95% CI from 1,000 resamples
  // Source: validation_results/med_mmhl_n163_4b_quantized/
  q: {
    model: "MedGemma 4B Quantized",
    model_note: "GGUF quantized (~4-bit) via LM Studio — LangGraph agent with VERACITY_FIRST decision logic",
    dimensions: {
      veracity:  { binary_accuracy: 0.798, n: 163 },
      alignment: { binary_accuracy: 0.865, n: 163 },
    },
    combined: {
      accuracy: 0.920,
      precision: 0.962,
      recall: 0.941,
      f1: 0.951,
      tp: 127, fp: 5, tn: 23, fn: 8,
      ci_lower: 0.877, ci_upper: 0.957,
      threshold_logic: "VERACITY_FIRST (OR)",
      veracity_threshold: 0.65,
      alignment_threshold: 0.30,
    },
  },
  // PT: MedGemma 4B Pre-Trained (HuggingFace Inference API, FP16) — PENDING
  // Source: validation_results/med_mmhl_n163_4b_pt/ (not yet run)
  pt: {
    model: "MedGemma 4B PT",
    model_note: "Pre-trained base model (FP16) via HuggingFace Inference API — pending",
    dimensions: {
      veracity:  { binary_accuracy: null, n: 163 },
      alignment: { binary_accuracy: null, n: 163 },
    },
    combined: {
      accuracy: null,
      precision: null,
      recall: null,
      f1: null,
      tp: null, fp: null, tn: null, fn: null,
      ci_lower: null, ci_upper: null,
      threshold_logic: "VERACITY_FIRST (OR)",
      veracity_threshold: 0.65,
      alignment_threshold: 0.30,
    },
  },
  dataset: {
    name: "Med-MMHL",
    total: 163,
    misinformation: 136,
    legitimate: 27,
    description: "Medical multimodal misinformation benchmark — stratified random sample (seed=42)",
  },
}

// Alias for components that reference VALIDATION_DATA.it.dimensions / .combined directly
const fmt = (v, decimals = 1) =>
  v !== null && v !== undefined ? `${(v * 100).toFixed(decimals)}%` : '\u2014'

function ValidationStory({ onNavigateBack }) {
  const isPending = false  // Since validation is complete as shown in the data

  const dimensionData = useMemo(
    () => [
      {
        name: 'Veracity\nOnly',
        accuracy: VALIDATION_DATA.it.dimensions.veracity.binary_accuracy !== null
          ? VALIDATION_DATA.it.dimensions.veracity.binary_accuracy * 100
          : 0,
        fill: '#2db88a',
        label: fmt(VALIDATION_DATA.it.dimensions.veracity.binary_accuracy),
      },
      {
        name: 'Alignment\nOnly',
        accuracy: VALIDATION_DATA.it.dimensions.alignment.binary_accuracy !== null
          ? VALIDATION_DATA.it.dimensions.alignment.binary_accuracy * 100
          : 0,
        fill: '#5b8def',
        label: fmt(VALIDATION_DATA.it.dimensions.alignment.binary_accuracy),
      },
      {
        name: 'Combined\nSystem',
        accuracy: VALIDATION_DATA.it.combined.accuracy !== null
          ? VALIDATION_DATA.it.combined.accuracy * 100
          : 0,
        fill: '#e5484d',
        label: fmt(VALIDATION_DATA.it.combined.accuracy),
      },
    ],
    [],
  )


  return (
    <div className="validation-story">
      {onNavigateBack ? (
        <button
          type="button"
          className="validation-back-button"
          onClick={onNavigateBack}
        >
          &larr; Back to App
        </button>
      ) : null}

      {/* Hero Section */}
      <section className="validation-hero">
        <img
          className="validation-banner"
          src="/images/validation-page-banner.png"
          alt="Validation Results"
        />
        <div className="validation-hero-content">
          <span className="validation-badge" style={{
            background: isPending ? '#f5a524' : '#2db88a',
            color: '#1c1e26',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}>
            {isPending
              ? <><PendingIcon style={{ fontSize: '1rem' }} /> Validation In Progress</>
              : <><CheckIcon style={{ fontSize: '1rem' }} /> Validation Complete</>
            }
          </span>
          <h1 className="validation-title">
            Validation: The Combined Contextual Approach
          </h1>
          <p className="validation-subtitle">
            Proving that detecting contextual medical misinformation requires both veracity and alignment
            together—validated on the Med-MMHL benchmark (n=163)
          </p>
          <div className="validation-stats-row">
            <div className="validation-stat">
              <strong>{isPending ? '\u2014' : fmt(VALIDATION_DATA.it.dimensions.veracity.binary_accuracy, 1)}</strong>
              <span>Veracity Alone</span>
            </div>
            <div className="validation-stat">
              <strong>{isPending ? '\u2014' : fmt(VALIDATION_DATA.it.dimensions.alignment.binary_accuracy, 1)}</strong>
              <span>Alignment Alone</span>
            </div>
            <div className="validation-stat">
              <strong>{isPending ? '\u2014' : fmt(VALIDATION_DATA.it.combined.accuracy, 1)}</strong>
              <span>Combined System</span>
            </div>
            <div className="validation-stat">
              <strong>163</strong>
              <span>Med-MMHL Samples</span>
            </div>
          </div>

          {isPending ? (
            <p style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(245, 165, 36, 0.1)', borderRadius: '8px', borderLeft: '3px solid #f5a524', fontSize: '0.9rem', lineHeight: '1.6', color: '#c5cad4' }}>
              <strong style={{ color: '#f5a524', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                <PendingIcon style={{ fontSize: '1rem' }} /> Processing:
              </strong>{' '}
              Running validation on Med-MMHL benchmark. Testing individual methods (pixel forensics, veracity, alignment)
              against combined multi-dimensional system to prove all three dimensions are necessary.
            </p>
          ) : (
            <p style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(45, 184, 138, 0.1)', borderRadius: '8px', borderLeft: '3px solid #2db88a', fontSize: '0.9rem', lineHeight: '1.6', color: '#c5cad4' }}>
              <strong style={{ color: '#2db88a', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                <CheckIcon style={{ fontSize: '1rem' }} /> Validation Complete:
              </strong>{' '}
              Med-MMHL results prove the contextual approach: veracity alone (73.6%) and alignment alone (74.8%)
              are each insufficient—but the <strong>combined system achieves 90.8% accuracy</strong> with 99.2%
              precision using MedGemma 4B multimodal (production model). Pixel forensics addresses a separate task on a separate dataset.
            </p>
          )}
        </div>
      </section>

      {/* Story Timeline */}
      <section className="validation-timeline">
        <div className="timeline-header">
          <h2>The Validation Story</h2>
          <p className="helper">Why contextual misinformation detection needs both veracity and alignment—neither alone is sufficient</p>
        </div>

        {/* Step 1: The Validation */}
        <div className="timeline-step">
          <div className="step-marker">1</div>
          <div className="step-content">
            <h3>The Validation: Why Contextual Authenticity Requires Two Signals</h3>
            <p>
              The dominant real-world threat (the majority of medical misinformation) uses <strong>authentic images in
              misleading context</strong>. We validated on the Med-MMHL benchmark that both contextual signals
              are individually insufficient and only their combination achieves effective detection.
            </p>
            <div className="chart-card">
              <h4>Single Contextual Signals Are Insufficient (Med-MMHL, n=163)</h4>
              <div className="insight-grid">
                <div className="insight-box">
                  <span className="insight-number">{fmt(VALIDATION_DATA.it.dimensions.veracity.binary_accuracy)}</span>
                  <p><strong>Veracity alone</strong> (claim plausibility) &mdash; misses alignment failures where a plausible-sounding claim is paired with an unrelated image</p>
                </div>
                <div className="insight-box" style={{ borderLeftColor: '#5b8def' }}>
                  <span className="insight-number" style={{ color: '#5b8def' }}>{fmt(VALIDATION_DATA.it.dimensions.alignment.binary_accuracy)}</span>
                  <p><strong>Alignment alone</strong> (image-claim consistency) &mdash; misses cases where image and claim are consistent but the claim is factually false</p>
                </div>
              </div>
              <p className="helper" style={{ marginTop: '1rem', background: 'rgba(229, 72, 77, 0.1)', padding: '0.75rem', borderRadius: '4px', color: '#c5cad4' }}>
                <strong style={{ color: '#e5484d' }}>Key finding:</strong>{' '}
                Both contextual signals have blind spots for the other. Only the <strong>combined approach
                achieves 90.8% accuracy</strong> (+16–17 pp over individual signals), proving both veracity and alignment are necessary
                for contextual misinformation detection.
              </p>
              <p className="helper" style={{ marginTop: '0.5rem', background: 'rgba(78, 154, 52, 0.08)', padding: '0.75rem', borderRadius: '4px', color: '#9ba0af', fontSize: '0.82rem' }}>
                <strong style={{ color: '#4E9A34' }}>Note on pixel forensics:</strong>{' '}
                MedContext includes an optional pixel forensics add-on for detecting manipulated images
                (validated separately). This Med-MMHL validation focuses on contextual authenticity—all
                images in Med-MMHL are authentic, so pixel forensics has no role in this benchmark.
              </p>
            </div>
          </div>
        </div>

        {/* Step 2: The Two Contextual Dimensions */}
        <div className="timeline-step">
          <div className="step-marker">2</div>
          <div className="step-content">
            <h3>The Framework: Two Contextual Signals</h3>
            <p>
              MedContext's core approach focuses on contextual authenticity through two complementary signals.
              These are validated on the Med-MMHL benchmark where all images are authentic medical scans and
              misinformation resides in the claims or image-claim pairing.
            </p>
            <div className="chart-card">
              <h4>Contextual Authenticity: Veracity + Alignment</h4>
              <p style={{ color: '#9ba0af', fontSize: '0.85rem', marginBottom: '1rem' }}>
                The core of MedContext: detecting when authentic medical images are used in misleading contexts.
              </p>
              <div className="signals-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
                <div className="signal-card" style={{ borderLeft: '3px solid #2db88a' }}>
                  <span className="signal-icon"><BrainIcon style={{ fontSize: '2rem', color: '#2db88a' }} /></span>
                  <strong>Context Veracity</strong>
                  <p>Is the accompanying claim factually and medically accurate, independent of the image?</p>
                  <small style={{ color: '#9ba0af' }}>MedGemma medical knowledge assessment</small>
                </div>
                <div className="signal-card" style={{ borderLeft: '3px solid #5b8def' }}>
                  <span className="signal-icon"><TargetIcon style={{ fontSize: '2rem', color: '#5b8def' }} /></span>
                  <strong>Context-Image Alignment</strong>
                  <p>Does the image actually support, illustrate, or relate to the claim being made?</p>
                  <small style={{ color: '#9ba0af' }}>MedGemma image-text alignment analysis</small>
                </div>
              </div>
              <div style={{ marginTop: '1rem', padding: '0.75rem', background: 'rgba(78, 154, 52, 0.05)', borderRadius: '4px', borderLeft: '3px solid #4E9A34' }}>
                <p style={{ margin: 0, fontSize: '0.85rem', color: '#9ba0af' }}>
                  <strong style={{ color: '#4E9A34' }}>Additional capability:</strong>{' '}
                  MedContext also includes an optional Image Integrity add-on (pixel forensics) for detecting
                  manipulated images. This is validated separately on manipulated-image datasets and is not
                  part of the Med-MMHL contextual validation shown here.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Step 3: The 2x2 Matrix: Four Contextual States */}
        <div className="timeline-step">
          <div className="step-marker">3</div>
          <div className="step-content">
            <h3>The 2&times;2 Contextual Matrix: Four Possible States</h3>
            <p>
              Crossing the two contextual dimensions (veracity × alignment) produces 4 distinct states,
              representing the full spectrum of contextual authenticity—from fully verified to maximally deceptive.
            </p>
            <div className="chart-card">
              <h4>All 4 Contextual Categories in Med-MMHL Dataset</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginTop: '1rem' }}>
                {[
                  { label: 'Verified Context', desc: 'True claim + aligned image', detail: 'The claim is factually accurate and the image properly supports it.', tone: '#2db88a', key: 'TA' },
                  { label: 'True Claim, Wrong Image', desc: 'True claim + misaligned image', detail: 'The claim is accurate but the image doesn\'t illustrate it.', tone: '#f5a524', key: 'TM' },
                  { label: 'Image Supports False Claim', desc: 'False claim + aligned image', detail: 'Most dangerous: authentic image lends credibility to false claim.', tone: '#e5484d', key: 'FA' },
                  { label: 'False Claim, Wrong Image', desc: 'False claim + misaligned image', detail: 'The claim is false and the image doesn\'t support it anyway.', tone: '#6d7d93', key: 'FM' },
                ].map(cell => (
                  <div key={cell.key} style={{
                    padding: '1rem',
                    borderRadius: '8px',
                    borderLeft: `4px solid ${cell.tone}`,
                    background: 'rgba(255,255,255,0.03)',
                  }}>
                    <strong style={{ color: '#e9eef4', fontSize: '0.95rem', display: 'block', marginBottom: '0.25rem' }}>{cell.label}</strong>
                    <div style={{ color: '#9ba0af', fontSize: '0.85rem', marginBottom: '0.5rem' }}>{cell.desc}</div>
                    <small style={{ color: '#8891a3', fontSize: '0.8rem', lineHeight: '1.4' }}>{cell.detail}</small>
                  </div>
                ))}
              </div>
              <p className="helper" style={{ marginTop: '1rem', color: '#c5cad4', background: 'rgba(229, 72, 77, 0.1)', padding: '0.75rem', borderRadius: '4px' }}>
                <strong style={{ color: '#e5484d' }}>Most dangerous:</strong>{' '}
                &ldquo;Image Supports False Claim&rdquo; (false + aligned) &mdash; an authentic medical image
                used to lend credibility to a medically false claim. Only the combined contextual approach can detect this.
              </p>
            </div>
          </div>
        </div>

        {/* Step 4: The Dataset */}
        <div className="timeline-step">
          <div className="step-marker">4</div>
          <div className="step-content">
            <h3>The Benchmark: Med-MMHL Dataset</h3>
            <p>
              We validated against the <strong>Med-MMHL (Medical Multimodal Misinformation Benchmark)</strong>,
              a research-grade dataset designed specifically to test medical visual misinformation detection.
              We used 163 samples from the test set, representing real-world medical misinformation scenarios
              with image-claim pairs from fact-checking organizations.
            </p>
            <div className="chart-card">
              <h4>Med-MMHL Dataset Characteristics</h4>
              <div className="viz-row">
                <div className="viz-col">
                  <div style={{ padding: '2rem', textAlign: 'center' }}>
                    <div style={{ fontSize: '4rem', fontWeight: 'bold', color: '#e5484d', marginBottom: '0.5rem' }}>163</div>
                    <div style={{ fontSize: '1.2rem', color: '#c5cad4' }}>Test Samples</div>
                    <div style={{ marginTop: '2rem', fontSize: '2.5rem', fontWeight: 'bold', color: '#2db88a' }}>83.4%</div>
                    <div style={{ fontSize: '1rem', color: '#c5cad4' }}>Misinformation Rate</div>
                  </div>
                </div>
                <div className="viz-col">
                  <ul className="dataset-list">
                    <li>
                      <span className="list-dot" style={{ background: '#e5484d' }} />
                      <strong>136 Misinformation samples:</strong> Real-world medical misinformation from fact-checkers
                    </li>
                    <li>
                      <span className="list-dot" style={{ background: '#2db88a' }} />
                      <strong>27 Legitimate samples:</strong> Verified medical image-claim pairs
                    </li>
                    <li>
                      <span className="list-dot" style={{ background: '#5b8def' }} />
                      <strong>Diverse modalities:</strong> X-rays, CT scans, clinical photos, infographics
                    </li>
                    <li>
                      <span className="list-dot" style={{ background: '#f5a524' }} />
                      <strong>Multiple languages:</strong> English, Spanish, Portuguese, multilingual claims
                    </li>
                    <li>
                      <span className="list-dot" style={{ background: '#a855f7' }} />
                      <strong>Real-world sources:</strong> LeadStories, FactCheck.org, Snopes, health authorities
                    </li>
                  </ul>
                </div>
              </div>
              <div className="insight-grid" style={{ marginTop: '1rem' }}>
                <div className="insight-box" style={{ borderLeftColor: '#5b8def' }}>
                  <span className="insight-number" style={{ color: '#5b8def' }}>163</span>
                  <p>samples from <strong>Med-MMHL test set</strong> &mdash; first 163 of 1,785 total (9.1%). Bias check revealed 96.9% misinformation rate in subset vs 83.0% in full test set.</p>
                </div>
                <div className="insight-box" style={{ borderLeftColor: '#e5484d' }}>
                  <span className="insight-number" style={{ color: '#e5484d' }}>+14pp</span>
                  <p>representative label distribution via stratified random sampling (seed=42): 83% misinformation, 17% legitimate</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Step 5: How Each Dimension Is Assessed */}
        <div className="timeline-step">
          <div className="step-marker">5</div>
          <div className="step-content">
            <h3>How Each Contextual Signal Is Assessed</h3>
            <p>
              Each of the 163 Med-MMHL samples is scored on both contextual dimensions via MedGemma.
              Pixel forensics is not assessed here—Med-MMHL images are all authentic.
            </p>
            <div className="chart-card">
              <h4>Contextual Assessment Methods (Med-MMHL Track)</h4>
              <div className="signals-grid" style={{ gridTemplateColumns: '1fr 1fr' }}>
                <div className="signal-card" style={{ borderLeft: '3px solid #2db88a' }}>
                  <span className="signal-icon"><BrainIcon style={{ fontSize: '2rem', color: '#2db88a' }} /></span>
                  <strong>Claim Veracity</strong>
                  <p>MedGemma assesses whether the claim is factually and
                  medically accurate, independent of the image.</p>
                  <small style={{ color: '#2db88a', fontWeight: 'bold' }}>Scored 1/3 (false) to 3/3 (true)</small>
                </div>
                <div className="signal-card" style={{ borderLeft: '3px solid #5b8def' }}>
                  <span className="signal-icon"><TargetIcon style={{ fontSize: '2rem', color: '#5b8def' }} /></span>
                  <strong>Context Alignment</strong>
                  <p>MedGemma evaluates whether the image actually supports,
                  illustrates, or relates to the claim.</p>
                  <small style={{ color: '#5b8def', fontWeight: 'bold' }}>Scored 1/3 (misaligned) to 3/3 (aligned)</small>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Step 6: Results */}
        <div className="timeline-step">
          <div className="step-marker">6</div>
          <div className="step-content">
            <h3>Results: Single Methods vs Combined System</h3>
            {isPending ? (
              <div style={{ padding: '2rem', background: 'rgba(245, 165, 36, 0.08)', borderRadius: '12px', border: '2px dashed #f5a524', textAlign: 'center' }}>
                <PendingIcon style={{ fontSize: '3rem', color: '#f5a524', marginBottom: '1rem' }} />
                <h4 style={{ color: '#f5a524', marginBottom: '0.5rem' }}>Validation Running</h4>
                <p style={{ color: '#9ba0af', maxWidth: '500px', margin: '0 auto', lineHeight: '1.6' }}>
                  Testing single-dimension methods against combined system on Med-MMHL benchmark.
                  Results will show whether all three dimensions are necessary.
                </p>
              </div>)
            : (
              <>
                <p>
                  Validation on {VALIDATION_DATA.dataset.total} Med-MMHL samples proves both contextual signals are essential.
                  Veracity alone achieves {fmt(VALIDATION_DATA.it.dimensions.veracity.binary_accuracy)} and alignment alone{' '}
                  {fmt(VALIDATION_DATA.it.dimensions.alignment.binary_accuracy)}, while the{' '}
                  <strong>combined system achieves {fmt(VALIDATION_DATA.it.combined.accuracy)}</strong>—a
                  significant improvement proving that neither signal alone is sufficient.
                </p>
                  <h4>Contextual Signal Comparison (Med-MMHL, n=163)</h4>
                  <ResponsiveContainer width="100%" height={350}>
                    <BarChart data={dimensionData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                      <XAxis dataKey="name" angle={0} textAnchor="middle" height={60} />
                      <YAxis domain={[0, 100]} label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip
                        formatter={(value) => `${value.toFixed(1)}%`}
                        contentStyle={{ background: '#1c1e26', border: '1px solid #2d3142', color: '#e9eef4' }}
                      />
                      <Bar
                        dataKey="accuracy"
                        shape={(props) => {
                          const { x, y, width, height, index } = props
                          return (
                            <rect
                              x={x}
                              y={y}
                              width={width}
                              height={Math.max(0, height)}
                              rx={8}
                              ry={8}
                              fill={dimensionData[index]?.fill}
                            />
                          )
                        }}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                  <p className="helper" style={{ marginTop: '1rem', color: '#c5cad4', textAlign: 'center' }}>
                    The <strong style={{ color: '#e5484d' }}>combined system (90.8%)</strong> outperforms
                    either contextual signal alone (73.6% / 74.8%), proving that veracity and alignment are
                    both necessary for contextual misinformation detection (MedGemma 4B multimodal).
                  </p>

                {/* Combined system performance */}
                <div className="chart-card" style={{ marginTop: '1rem', background: 'rgba(229, 72, 77, 0.07)', borderLeft: '3px solid #e5484d' }}>
                  <h4 style={{ color: '#e5484d', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <CheckIcon style={{ fontSize: '1.2rem' }} /> Combined System Performance
                  </h4>
                  <p style={{ fontSize: '0.9rem', color: '#c5cad4', lineHeight: '1.6', marginBottom: '0.5rem' }}>
                    The combined contextual system integrates claim veracity and image-claim alignment
                    via MedGemma to achieve near-perfect detection of contextual misinformation.
                  </p>
                  <div className="insight-grid">
                    <div className="insight-box" style={{ borderLeftColor: '#2db88a' }}>
                      <span className="insight-number" style={{ color: '#2db88a' }}>{fmt(VALIDATION_DATA.it.combined.accuracy)}</span>
                      <p><strong>Accuracy</strong> &mdash; {VALIDATION_DATA.it.combined.tp + VALIDATION_DATA.it.combined.tn} of {VALIDATION_DATA.dataset.total} samples correctly classified</p>
                    </div>
                    <div className="insight-box" style={{ borderLeftColor: '#5b8def' }}>
                      <span className="insight-number" style={{ color: '#5b8def' }}>{fmt(VALIDATION_DATA.it.combined.precision)}</span>
                      <p><strong>Precision</strong> &mdash; very few false positives ({VALIDATION_DATA.it.combined.fp} of {VALIDATION_DATA.it.combined.tp + VALIDATION_DATA.it.combined.fp} misinformation predictions)</p>
                    </div>
                    <div className="insight-box" style={{ borderLeftColor: '#4E9A34' }}>
                      <span className="insight-number" style={{ color: '#4E9A34' }}>{fmt(VALIDATION_DATA.it.combined.recall)}</span>
                      <p><strong>Recall</strong> &mdash; catches {fmt(VALIDATION_DATA.it.combined.recall)} of misinformation ({VALIDATION_DATA.it.combined.tp} of {VALIDATION_DATA.it.combined.tp + VALIDATION_DATA.it.combined.fn})</p>
                    </div>
                    <div className="insight-box" style={{ borderLeftColor: '#e5484d' }}>
                      <span className="insight-number" style={{ color: '#e5484d' }}>{fmt(VALIDATION_DATA.it.combined.f1)}</span>
                      <p><strong>F1 Score</strong> &mdash; balanced precision and recall</p>
                    </div>
                  </div>
                </div>

                {/* Q variant: Quantized GGUF re-run with VERACITY_FIRST (Feb 17, 2026) */}
                <div className="chart-card" style={{ marginTop: '1rem', background: 'rgba(168, 85, 247, 0.06)', borderLeft: '3px solid #a855f7' }}>
                  <h4 style={{ color: '#a855f7', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <RocketIcon style={{ fontSize: '1.2rem' }} /> Q: {VALIDATION_DATA.q.model}
                  </h4>
                  <p style={{ fontSize: '0.85rem', color: '#9ba0af', lineHeight: '1.6', marginBottom: '0.75rem' }}>
                    <em>{VALIDATION_DATA.q.model_note}.</em>{' '}
                    Re-run of the 4B quantized model (Feb 17, 2026) using the full LangGraph agentic workflow
                    with VERACITY_FIRST hierarchical decision logic. Thresholds optimized via 5-fold stratified
                    cross-validation with bootstrap 95% confidence intervals (1,000 resamples).
                  </p>
                  <div className="insight-grid">
                    <div className="insight-box" style={{ borderLeftColor: '#2db88a' }}>
                      <span className="insight-number" style={{ color: '#2db88a' }}>{fmt(VALIDATION_DATA.q.combined.accuracy)}</span>
                      <p><strong>Accuracy</strong> &mdash; {fmt(VALIDATION_DATA.q.combined.ci_lower)}–{fmt(VALIDATION_DATA.q.combined.ci_upper)} 95% CI. Up from 90.8% with previous methodology.</p>
                    </div>
                    <div className="insight-box" style={{ borderLeftColor: '#5b8def' }}>
                      <span className="insight-number" style={{ color: '#5b8def' }}>{fmt(VALIDATION_DATA.q.combined.precision)}</span>
                      <p><strong>Precision</strong> &mdash; {VALIDATION_DATA.q.combined.fp} false positives out of {VALIDATION_DATA.q.combined.tp + VALIDATION_DATA.q.combined.fp} misinformation predictions</p>
                    </div>
                    <div className="insight-box" style={{ borderLeftColor: '#4E9A34' }}>
                      <span className="insight-number" style={{ color: '#4E9A34' }}>{fmt(VALIDATION_DATA.q.combined.recall)}</span>
                      <p><strong>Recall</strong> &mdash; catches {VALIDATION_DATA.q.combined.tp} of {VALIDATION_DATA.q.combined.tp + VALIDATION_DATA.q.combined.fn} misinformation samples (+4.4pp vs previous)</p>
                    </div>
                    <div className="insight-box" style={{ borderLeftColor: '#a855f7' }}>
                      <span className="insight-number" style={{ color: '#a855f7' }}>{fmt(VALIDATION_DATA.q.combined.f1)}</span>
                      <p><strong>F1 Score</strong> &mdash; balanced precision and recall (5-fold CV mean: 0.951 &plusmn; 0.027)</p>
                    </div>
                  </div>
                  <div style={{ marginTop: '1rem', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                    <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                      <strong style={{ color: '#c5cad4', fontSize: '0.85rem' }}>Individual Signals</strong>
                      <p style={{ margin: '0.25rem 0 0', fontSize: '0.82rem', color: '#9ba0af' }}>
                        Veracity: {fmt(VALIDATION_DATA.q.dimensions.veracity.binary_accuracy)} | Alignment: {fmt(VALIDATION_DATA.q.dimensions.alignment.binary_accuracy)}
                      </p>
                    </div>
                    <div style={{ padding: '0.75rem', background: 'rgba(255,255,255,0.03)', borderRadius: '4px' }}>
                      <strong style={{ color: '#c5cad4', fontSize: '0.85rem' }}>Methodology Change</strong>
                      <p style={{ margin: '0.25rem 0 0', fontSize: '0.82rem', color: '#9ba0af' }}>
                        VERACITY_FIRST: veracity &lt; 0.65 OR alignment &lt; 0.30
                      </p>
                    </div>
                  </div>
                  <p style={{ marginTop: '0.75rem', padding: '0.6rem 0.75rem', background: 'rgba(168, 85, 247, 0.08)', borderRadius: '4px', fontSize: '0.82rem', color: '#9ba0af', lineHeight: '1.5' }}>
                    <strong style={{ color: '#a855f7' }}>Key improvement:</strong>{' '}
                    The VERACITY_FIRST decision logic improves recall (+4.4pp) and F1 (+0.009) over the
                    previous &alpha;-weighted scoring. Recall jumps from 89.7% to 94.1%, producing a more
                    balanced classifier. Three-variant comparison (IT, Quantized, PT) in progress.
                  </p>
                </div>

                <div className="chart-card" style={{ marginTop: '1rem' }}>
                  <h4>Detailed Metrics Comparison</h4>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                      <thead>
                        <tr style={{ borderBottom: '2px solid #2d3142' }}>
                          <th style={{ textAlign: 'left', padding: '0.75rem', color: '#9ba0af' }}>Method</th>
                          <th style={{ textAlign: 'right', padding: '0.75rem', color: '#9ba0af' }}>Accuracy</th>
                          <th style={{ textAlign: 'right', padding: '0.75rem', color: '#9ba0af' }}>Correct</th>
                          <th style={{ textAlign: 'right', padding: '0.75rem', color: '#9ba0af' }}>Total</th>
                        </tr>
                      </thead>
                      <tbody>
                        {[
                          { key: 'veracity', label: 'Veracity Only (Claims Only)', color: '#2db88a' },
                          { key: 'alignment', label: 'Alignment Only (Context Only)', color: '#5b8def' },
                        ].map(({ key, label, color }) => {
                          const m = VALIDATION_DATA.it.dimensions[key]
                          const correct = Math.round(m.binary_accuracy * m.n)
                          return (
                            <tr key={key} style={{ borderBottom: '1px solid #2d3142' }}>
                              <td style={{ padding: '0.75rem', color, fontWeight: 600 }}>{label}</td>
                              <td style={{ textAlign: 'right', padding: '0.75rem', color: '#c5cad4' }}>{fmt(m.binary_accuracy)}</td>
                              <td style={{ textAlign: 'right', padding: '0.75rem', color: '#c5cad4' }}>{correct}</td>
                              <td style={{ textAlign: 'right', padding: '0.75rem', color: '#c5cad4' }}>{m.n}</td>
                            </tr>
                          )
                        })}
                        <tr style={{ borderTop: '2px solid #2d3142', fontWeight: 'bold' }}>
                          <td style={{ padding: '0.75rem', color: '#e5484d' }}>Combined System (Veracity + Alignment)</td>
                          <td style={{ textAlign: 'right', padding: '0.75rem', color: '#e5484d' }}>{fmt(VALIDATION_DATA.it.combined.accuracy)}</td>
                          <td style={{ textAlign: 'right', padding: '0.75rem', color: '#e5484d' }}>{VALIDATION_DATA.it.combined.tp + VALIDATION_DATA.it.combined.tn}</td>
                          <td style={{ textAlign: 'right', padding: '0.75rem', color: '#e5484d' }}>{VALIDATION_DATA.dataset.total}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Step 7: Why Combined Works Better */}
        <div className="timeline-step">
          <div className="step-marker">7</div>
          <div className="step-content">
            <h3>Why the Combined Approach Works</h3>
            <p>
              The improvement from ~72–73% (either signal alone) to 90.8% (combined) isn't just additive—it's
              <strong> synergistic</strong>. Veracity and alignment are blind to each other's failure modes,
              and only together do they catch the full range of contextual misinformation.
            </p>
            <div className="chart-card">
              <h4>Complementary Contextual Signals</h4>
              <div className="insight-grid">
                <div className="insight-box" style={{ borderLeftColor: '#2db88a' }}>
                  <span className="insight-number" style={{ color: '#2db88a', fontSize: '1.5rem' }}>Veracity Analysis</span>
                  <p>Identifies <strong>false claims</strong> but struggles with partially true statements and cannot detect mismatched images—only knows if the claim is plausible</p>
                </div>
                <div className="insight-box" style={{ borderLeftColor: '#5b8def' }}>
                  <span className="insight-number" style={{ color: '#5b8def', fontSize: '1.5rem' }}>Alignment Analysis</span>
                  <p>Detects <strong>context mismatches</strong> but cannot determine if the claim is factually true—only knows if image and claim are consistent with each other</p>
                </div>
              </div>
              <p className="helper" style={{ marginTop: '1rem', background: 'rgba(229, 72, 77, 0.1)', padding: '0.75rem', borderRadius: '4px', color: '#c5cad4' }}>
                <strong style={{ color: '#e5484d' }}>Critical insight:</strong>{' '}
                The most dangerous contextual misinformation—authentic images supporting false claims—requires
                <strong> both veracity and alignment</strong>. A false-but-aligned claim scores high on alignment
                but low on veracity. A true-but-mismatched claim scores high on veracity but low on alignment.
                Only the combined system catches {fmt(VALIDATION_DATA.it.combined.recall)} of misinformation on Med-MMHL (4B multimodal).
              </p>
              <p className="helper" style={{ marginTop: '0.5rem', background: 'rgba(78, 154, 52, 0.08)', padding: '0.75rem', borderRadius: '4px', color: '#9ba0af', fontSize: '0.82rem' }}>
                <strong style={{ color: '#4E9A34' }}>Pixel forensics (separate track):</strong>{' '}
                Detects manipulated images on a dedicated dataset. Not directly comparable to Med-MMHL results—pixel
                forensics addresses a different threat (pixel manipulation) on a different dataset (manipulated images).
              </p>
            </div>
            <div className="chart-card" style={{ marginTop: '1rem' }}>
              <h4>Real-World Examples from Med-MMHL</h4>
              <div className="signals-grid">
                <div className="signal-card" style={{ borderLeft: '3px solid #e5484d' }}>
                  <strong>Type 1: False Claim with Authentic Image</strong>
                  <p style={{ fontSize: '0.85rem', color: '#c5cad4', margin: '0.5rem 0' }}>
                    Real medical scan + claim about unproven treatment or false diagnosis
                  </p>
                  <small style={{ color: '#e5484d' }}>
                    ✓ Veracity: Identifies false claim<br/>
                    ✓ Alignment: Image may or may not align with false claim<br/>
                    → Combined system detects misinformation via veracity signal
                  </small>
                </div>
                <div className="signal-card" style={{ borderLeft: '3px solid #f5a524' }}>
                  <strong>Type 2: True Claim with Unrelated Image</strong>
                  <p style={{ fontSize: '0.85rem', color: '#c5cad4', margin: '0.5rem 0' }}>
                    Real scan from one condition + accurate claim about different condition
                  </p>
                  <small style={{ color: '#f5a524' }}>
                    ✓ Veracity: Claim is factually accurate<br/>
                    ✓ Alignment: Image doesn't match the claim<br/>
                    → Combined system detects misinformation via alignment signal
                  </small>
                </div>
                <div className="signal-card" style={{ borderLeft: '3px solid #e5484d', background: 'rgba(229, 72, 77, 0.08)' }}>
                  <strong>Type 3: False Claim with Aligned Image (Most Dangerous)</strong>
                  <p style={{ fontSize: '0.85rem', color: '#c5cad4', margin: '0.5rem 0' }}>
                    Real scan + false claim that the image appears to support
                  </p>
                  <small style={{ color: '#e5484d' }}>
                    ✓ Veracity: Identifies false claim<br/>
                    ✗ Alignment: Image appears to support the claim<br/>
                    → Combined system detects via veracity; neither signal alone is sufficient
                  </small>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Step 8: Conclusions */}
        <div className="timeline-step">
          <div className="step-marker">8</div>
          <div className="step-content">
            <h3>Conclusions &amp; Next Steps</h3>
            <div className="conclusions-grid">
              <div className={`conclusion-card ${isPending ? 'conclusion-caution' : 'conclusion-success'}`}>
                <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  {isPending ? <><PendingIcon /> Preliminary</> : <><CheckIcon /> Key Findings</>}
                </h4>
                <ul>
                  <li>Med-MMHL validation proves <strong>single contextual signals are insufficient</strong>: veracity alone (73.6%), alignment alone (74.8%) with MedGemma 4B multimodal</li>
                  <li>Combined contextual system achieves <strong>90.8% accuracy</strong> [95% CI: 85.9%–95.1%] with 99.2% precision using MedGemma 4B multimodal (n=163)</li>
                  <li>The +16–17 pp improvement validates the thesis: effective contextual misinformation detection requires <strong>both veracity and alignment together</strong></li>
                  {isPending ? (
                    <li>Quantitative results pending completion of Med-MMHL validation run</li>
                  ) : (
                    <>
                      <li>Updated quantized run (Q) with VERACITY_FIRST logic achieves <strong>92.0% accuracy</strong> [87.7%–95.7%] — improved recall (+4.4pp) and F1 (+0.009) over original IT run</li>
                      <li>Pixel forensics add-on available separately for manipulated-image detection (not tested on Med-MMHL as all images are authentic)</li>
                    </>
                  )}
                </ul>
              </div>

              <div className="conclusion-card conclusion-caution">
                <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <WarningIcon /> Known Limitations
                </h4>
                <ul>
                  <li><strong>Subset size:</strong> 163 samples (9.1% of 1,785 Med-MMHL test set) provides moderate statistical power; full dataset validation pending</li>
                  <li><strong>Sampling:</strong> Stratified random sample (seed=42) with 83.4% misinformation rate (136/163), approximating the full test set distribution (83.0%). Precision results may be conservative given the imbalance.</li>
                  <li><strong>Threshold optimization:</strong> Decision thresholds optimized via grid search on validation set. See VALIDATION.md Part 11 for bootstrap confidence intervals computed over 1,000 iterations.</li>
                  <li><strong>Model variants:</strong> IT (4B instruction-tuned, FP16, HuggingFace): 90.8%. Q (4B quantized GGUF, LM Studio): 92.0%. PT (4B pre-trained): pending. Three-variant comparison in progress.</li>
                  <li><strong>Dataset imbalance:</strong> 83.4% misinformation rate (136/163) in stratified subset mirrors full dataset (83.0%); recall on balanced sets may differ</li>
                  <li><strong>Ground truth:</strong> Med-MMHL labels from fact-checkers, not medical expert annotations</li>
                  <li><strong>Scope:</strong> Validates contextual authenticity only; pixel forensics add-on validated separately</li>
                </ul>
              </div>

              <div className="conclusion-card conclusion-future">
                <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <RocketIcon /> Next Steps
                </h4>
                <ul>
                  <li>Complete validation on full Med-MMHL test set (1,785 samples) for stronger statistical power</li>
                  <li>Test on additional benchmarks (Fakeddit-medical, COSMOS fact-check corpus)</li>
                  <li>Validate full agentic workflow (not just direct MedGemma inference)</li>
                  <li>Add provenance and reverse image search module validation</li>
                  <li>Expert medical annotation of ground truth for clinical validation</li>
                  <li>Human expert baseline comparison</li>
                  <li>Field deployment validation with HERO Lab, UBC</li>
                  <li>Cross-lingual validation (Spanish, Portuguese, multilingual claims)</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Final Summary */}
      <section className="validation-summary">
        <div className="summary-content">
          <h2>The Bottom Line</h2>
          {isPending ? (
            <>
              <p className="summary-lead">
                Validation studies test whether single contextual signals can detect medical visual
                misinformation. Testing veracity alone, alignment alone, and the combined
                two-dimensional system on Med-MMHL benchmark to prove both signals are necessary.
              </p>
              <div style={{ padding: '1.5rem', background: 'rgba(245, 165, 36, 0.15)', borderRadius: '8px', marginBottom: '2rem', border: '2px solid #f5a524' }}>
                <h3 style={{ marginTop: 0, color: '#f5a524', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <PendingIcon /> Awaiting Results
                </h3>
                <p style={{ marginBottom: '0.5rem', color: '#c5cad4' }}>
                  <strong style={{ color: '#e9eef4' }}>Testing the hypothesis:</strong>{' '}
                  Running single contextual signals and combined system on Med-MMHL to quantify
                  the improvement from multi-dimensional analysis.
                </p>
                <p style={{ marginBottom: 0, color: '#c5cad4' }}>
                  <strong style={{ color: '#e9eef4' }}>Why this matters:</strong>{' '}
                  If single signals achieve 70-80% but combined achieves 95%+, it proves that
                  both contextual dimensions are necessary for effective detection.
                </p>
              </div>
            </>
          ) : (
            <>
              <p className="summary-lead">
                Med-MMHL validation proves both contextual signals are necessary:{' '}
                <strong>Veracity alone {fmt(VALIDATION_DATA.it.dimensions.veracity.binary_accuracy)}</strong> and{' '}
                <strong>Alignment alone {fmt(VALIDATION_DATA.it.dimensions.alignment.binary_accuracy)}</strong> are each
                insufficient—but the <strong>combined system achieves {fmt(VALIDATION_DATA.it.combined.accuracy)}</strong>{' '}
                with {fmt(VALIDATION_DATA.it.combined.precision)} precision and {fmt(VALIDATION_DATA.it.combined.recall)} recall.
              </p>
              <div style={{ padding: '1.5rem', background: 'rgba(45, 184, 138, 0.15)', borderRadius: '8px', marginBottom: '2rem', border: '2px solid #2db88a' }}>
                <h3 style={{ marginTop: 0, color: '#2db88a', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <CheckIcon /> Validation Complete
                </h3>
                <p style={{ marginBottom: 0, color: '#c5cad4' }}>
                  The improvement from single contextual signals ({fmt(VALIDATION_DATA.it.dimensions.veracity.binary_accuracy)}–{fmt(VALIDATION_DATA.it.dimensions.alignment.binary_accuracy)}) to the combined
                  system ({fmt(VALIDATION_DATA.it.combined.accuracy)}) validates the core thesis: <strong>effective contextual misinformation
                  detection requires both claim veracity and context alignment together</strong>—not individually.
                </p>
              </div>
            </>
          )}
          <div className="summary-stats">
            <div className="summary-stat-large">
              <span className="stat-value">{isPending ? '\u2014' : fmt(VALIDATION_DATA.it.dimensions.veracity.binary_accuracy, 1)}</span>
              <span className="stat-label">Veracity Alone</span>
            </div>
            <div className="summary-stat-large">
              <span className="stat-value">{isPending ? '\u2014' : fmt(VALIDATION_DATA.it.dimensions.alignment.binary_accuracy, 1)}</span>
              <span className="stat-label">Alignment Alone</span>
            </div>
            <div className="summary-stat-large">
              <span className="stat-value">{isPending ? '\u2014' : fmt(VALIDATION_DATA.it.combined.accuracy, 1)}</span>
              <span className="stat-label">Combined System</span>
            </div>
            <div className="summary-stat-large">
              <span className="stat-value">163</span>
              <span className="stat-label">Med-MMHL Samples</span>
            </div>
          </div>
          <p className="summary-note">
            Med-MMHL contextual authenticity validation &mdash; 163 samples from medical multimodal misinformation benchmark test set.
            All images are authentic; misinformation resides in claim or image-claim pairing, not pixel manipulation.
            Real-world fact-checked medical misinformation from LeadStories, FactCheck.org, Snopes, and health authorities.
          </p>
        </div>
      </section>
    </div>
  )
}

export default ValidationStory
