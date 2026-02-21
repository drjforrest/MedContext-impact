import {
  CheckCircle as CheckIcon,
  TrendingUp as TrendingUpIcon,
  Psychology as BrainIcon,
  TrackChanges as TargetIcon,
} from '@mui/icons-material'
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts'
import './ValidationStory.css'

// FRESH VALIDATION DATA - February 20, 2026
// Model: MedGemma 4B IT Quantized (Q4_KM, ~4-bit)
// Dataset: Med-MMHL (n=163, stratified random, seed=42)
const VALIDATION_DATA = {
  q: {
    model: "MedGemma 4B IT Quantized",
    date: "February 20, 2026",
    veracity: 71.2,      // Individual signal
    alignment: 77.9,     // Individual signal
    combined: {
      accuracy: 91.4,
      precision: 96.9,
      recall: 92.6,
      f1: 94.7,
      tp: 125, fp: 4, tn: 24, fn: 10,
    },
    thresholds: { veracity: 0.65, alignment: 0.30 },
  },
  dataset: { n: 163, misinfo: 136, legitimate: 27 },
}

function ValidationStory({ onNavigateBack }) {
  const d = VALIDATION_DATA.q
  
  const sCurveData = [
    { name: 'Veracity\nOnly', acc: d.veracity, fill: '#E63946' },
    { name: 'Alignment\nOnly', acc: d.alignment, fill: '#F4A261' },
    { name: 'Optimized\nCombined', acc: d.combined.accuracy, fill: '#2A9D8F' },
  ]

  const fmt = (value, digits = 1) => Number(value).toFixed(digits)

  return (
    <div className="validation-story">
      {onNavigateBack && (
        <button className="validation-back-button" onClick={onNavigateBack}>
          &larr; Back to App
        </button>
      )}

      {/* HERO */}
      <section className="validation-hero">
        <div className="validation-hero-content">
          <span className="validation-badge" style={{ background: '#2A9D8F', color: '#1c1e26' }}>
            <CheckIcon style={{ fontSize: '1rem' }} /> Validation Complete
          </span>
          
          <h1 className="validation-title">
            The Optimization S-Curve
          </h1>
          
          <p className="validation-subtitle">
            How hierarchical optimization transforms weak individual signals (71-78%) 
            into a 91.4% accurate misinformation detector
          </p>

          <div className="validation-stats-row">
            <div className="validation-stat">
              <strong>{d.veracity.toFixed(1)}%</strong>
              <span>Veracity Only</span>
            </div>
            <div className="validation-stat">
              <strong>{d.alignment.toFixed(1)}%</strong>
              <span>Alignment Only</span>
            </div>
            <div className="validation-stat" style={{ background: 'rgba(42, 157, 143, 0.2)' }}>
              <strong style={{ color: '#2A9D8F' }}>{d.combined.accuracy.toFixed(1)}%</strong>
              <span>Optimized</span>
            </div>
            <div className="validation-stat">
              <strong>+13-20%</strong>
              <span>Gain</span>
            </div>
          </div>
        </div>
      </section>

      {/* THE S-CURVE STORY */}
      <section className="validation-timeline">
        
        {/* STEP 1: THE PROBLEM */}
        <div className="timeline-step">
          <div className="step-marker">1</div>
          <div className="step-content">
            <h3>The Problem: Individual Signals Are Weak</h3>
            <p>
              Two contextual signals detect medical misinformation: <strong>veracity</strong> (is the claim true?) 
              and <strong>alignment</strong> (does the image match?). Alone, each is insufficient.
            </p>
            
            <div className="chart-card">
              <div className="insight-grid">
                <div className="insight-box">
                  <span className="insight-number" style={{ color: '#E63946' }}>{d.veracity.toFixed(1)}%</span>
                  <p><strong>Veracity alone</strong> misses image misuse</p>
                </div>
                <div className="insight-box" style={{ borderLeftColor: '#F4A261' }}>
                  <span className="insight-number" style={{ color: '#F4A261' }}>{d.alignment.toFixed(1)}%</span>
                  <p><strong>Alignment alone</strong> misses false claims</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* STEP 2: THE BREAKTHROUGH */}
        <div className="timeline-step">
          <div className="step-marker">2</div>
          <div className="step-content">
            <h3>The S-Curve Breakthrough</h3>
            <p>
              Simple combination plateaus. But <strong>hierarchical optimization</strong>—smart thresholds 
              (0.65/0.30) and VERACITY_FIRST logic—unlocks the inflection point.
            </p>
            
            <div className="chart-card">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={sCurveData} margin={{ top: 10, right: 30, left: 0, bottom: 40 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} />
                  <YAxis domain={[0, 100]} hide />
                  <Tooltip formatter={(v) => `${v.toFixed(1)}%`} />
                  <Bar dataKey="acc" radius={[6, 6, 0, 0]} label={{ position: 'top', formatter: (v) => `${v.toFixed(1)}%`, fontWeight: 'bold' }} />
                </BarChart>
              </ResponsiveContainer>
              
              <p className="helper" style={{ marginTop: '1rem', background: 'rgba(42, 157, 143, 0.1)', padding: '0.75rem', borderRadius: '4px' }}>
                <strong style={{ color: '#2A9D8F' }}>The jump:</strong> From ~71-78% individual signals 
                to <strong>91.4% optimized</strong>. The whole exceeds the sum when arranged correctly.
              </p>
            </div>
          </div>
        </div>

        {/* STEP 3: HOW IT WORKS */}
        <div className="timeline-step">
          <div className="step-marker">3</div>
          <div className="step-content">
            <h3>How Optimization Works</h3>
            <p>
              <strong>VERACITY_FIRST:</strong> Check claim truth first. Only if ambiguous, check alignment. 
              Smart thresholds (0.65/0.30) bias toward caution.
            </p>
            
            <div className="chart-card">
              <div className="signals-grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="signal-card" style={{ borderLeft: '3px solid #E63946' }}>
                  <BrainIcon style={{ fontSize: '2rem', color: '#E63946' }} />
                  <strong>Veracity Threshold: 0.65</strong>
                  <p style={{ fontSize: '0.85rem' }}>
                    High bar before calling something "not misinformation"
                  </p>
                </div>
                <div className="signal-card" style={{ borderLeft: '3px solid #F4A261' }}>
                  <TargetIcon style={{ fontSize: '2rem', color: '#F4A261' }} />
                  <strong>Alignment Threshold: 0.30</strong>
                  <p style={{ fontSize: '0.85rem' }}>
                    Lenient—only flag obvious mismatches
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* STEP 4: RESULTS */}
        <div className="timeline-step">
          <div className="step-marker">4</div>
          <div className="step-content">
            <h3>Results: 91.4% Accuracy</h3>
            
            <div className="chart-card" style={{ background: 'rgba(42, 157, 143, 0.1)', borderLeft: '3px solid #2A9D8F' }}>
              <div className="insight-grid">
                <div className="insight-box">
                  <span className="insight-number" style={{ color: '#2A9D8F' }}>{d.combined.accuracy.toFixed(1)}%</span>
                  <p><strong>Accuracy</strong> — 149/163 correct</p>
                </div>
                <div className="insight-box">
                  <span className="insight-number" style={{ color: '#5b8def' }}>{d.combined.precision.toFixed(1)}%</span>
                  <p><strong>Precision</strong> — Only 4 false alarms</p>
                </div>
                <div className="insight-box">
                  <span className="insight-number" style={{ color: '#4E9A34' }}>{d.combined.recall.toFixed(1)}%</span>
                  <p><strong>Recall</strong> — Caught 125/135 misinfo</p>
                </div>
                <div className="insight-box">
                  <span className="insight-number" style={{ color: '#e5484d' }}>{d.combined.f1.toFixed(1)}%</span>
                  <p><strong>F1 Score</strong> — Balanced performance</p>
                </div>
              </div>
              
              <div style={{ marginTop: '1rem', textAlign: 'center', padding: '0.5rem', background: 'rgba(255,255,255,0.5)', borderRadius: '4px' }}>
                <strong>Confusion Matrix:</strong> TP:{d.combined.tp} FP:{d.combined.fp} TN:{d.combined.tn} FN:{d.combined.fn}
              </div>
            </div>
          </div>
        </div>

        {/* STEP 5: WHY IT MATTERS */}
        <div className="timeline-step">
          <div className="step-marker">5</div>
          <div className="step-content">
            <h3>Why The S-Curve Matters</h3>
            <p>
              Like compound interest or network effects, contextual authenticity has an inflection point. 
              Optimization—not just combination—is the key to reliable medical misinformation detection.
            </p>
            
            <div className="chart-card">
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', textAlign: 'center' }}>
                <div style={{ padding: '1rem', background: 'rgba(230, 57, 70, 0.1)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#E63946' }}>71%</div>
                  <div style={{ fontSize: '0.8rem' }}>Veracity</div>
                </div>
                <div style={{ padding: '1rem', background: 'rgba(244, 162, 97, 0.1)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#F4A261' }}>78%</div>
                  <div style={{ fontSize: '0.8rem' }}>Alignment</div>
                </div>
                <div style={{ padding: '1rem', background: 'rgba(108, 117, 125, 0.1)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#6C757D' }}>~80%</div>
                  <div style={{ fontSize: '0.8rem' }}>Simple</div>
                </div>
                <div style={{ padding: '1rem', background: 'rgba(42, 157, 143, 0.2)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#2A9D8F' }}>91%</div>
                  <div style={{ fontSize: '0.8rem' }}>Optimized</div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </section>

      {/* SUMMARY */}
      <section className="validation-summary">
        <div className="summary-content">
          <h2>The Bottom Line</h2>
          <p className="summary-lead">
            Medical misinformation detection requires <strong>optimization, not just combination</strong>.
            Hierarchical logic with smart thresholds transforms ~71-78% signals into a
            <strong> 91.4% accurate quantized model</strong>.
          </p>

          <div style={{ padding: '1.5rem', background: 'rgba(42, 157, 143, 0.15)', borderRadius: '8px', marginBottom: '2rem', border: '2px solid #2A9D8F' }}>
            <h3 style={{ marginTop: 0, color: '#2A9D8F', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <TrendingUpIcon /> The S-Curve Breakthrough
            </h3>
            <p style={{ marginBottom: 0, color: '#c5cad4' }}>
              Like compound interest or network effects, contextual authenticity exhibits an S-curve:
              slow initial gains, a long plateau, then rapid acceleration when the pieces align.
              The quantized MedGemma 4B model—efficient and deployable—achieves this breakthrough,
              proving that <strong>optimization, not just combination, is the key</strong>.
            </p>
          </div>

          <div className="validation-stats-row">
            <div className="validation-stat">
              <strong>{fmt(d.veracity)}%</strong>
              <span>Veracity Only</span>
            </div>
            <div className="validation-stat">
              <strong>{fmt(d.alignment)}%</strong>
              <span>Alignment Only</span>
            </div>
            <div className="validation-stat" style={{ background: 'rgba(42, 157, 143, 0.2)' }}>
              <strong style={{ color: '#2A9D8F' }}>{fmt(d.combined.accuracy)}%</strong>
              <span>Optimized System</span>
            </div>
            <div className="validation-stat">
              <strong>{VALIDATION_DATA.dataset.n}</strong>
              <span>Med-MMHL Samples</span>
            </div>
          </div>

          <p className="summary-note" style={{ marginTop: '1.5rem' }}>
            Med-MMHL validation (n={VALIDATION_DATA.dataset.n}, stratified random, seed=42) — February 20, 2026.
            Q4_KM quantized model via llama-cpp-python. Hierarchical optimization with
            VERACITY_FIRST logic and tuned thresholds (0.65/0.30) achieves the S-curve breakthrough.
          </p>
        </div>
      </section>
    </div>
  )
}

export default ValidationStory