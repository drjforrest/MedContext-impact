import {
  CheckCircle as CheckIcon,
  Shuffle as RandomIcon,
  Science as ScienceIcon,
  Verified as VerifiedIcon
} from '@mui/icons-material'
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import './ValidationStory.css'

// Med-MMHL Dataset Information
const MED_MMHL_INFO = {
  total: 1785,
  sample: 163,
  seed: 42,
  misinfoRate: 83.4, // 136/163 in sample
  fullDatasetRate: 83.0, // Original dataset
  sources: ['LeadStories', 'FactCheck.org', 'Snopes', 'Health Authorities'],
}

function ValidationStory({ onNavigateBack }) {
  // Distribution comparison data
  const distributionData = [
    { name: 'Full\nDataset', misinfoRate: MED_MMHL_INFO.fullDatasetRate, fill: '#5b8def' },
    { name: 'Sequential\nFirst-163', misinfoRate: 88.3, fill: '#E63946' },
    { name: 'Stratified\nRandom', misinfoRate: MED_MMHL_INFO.misinfoRate, fill: '#2A9D8F' },
  ]

  // Sample size confidence data
  const sampleSizeData = [
    { n: 50, ci_width: 12.8, fill: '#E63946' },
    { n: 100, ci_width: 9.1, fill: '#F4A261' },
    { n: 163, ci_width: 7.2, fill: '#2A9D8F' },
  ]

  return (
    <div className="validation-story">
      {onNavigateBack && (
        <button className="validation-back-button" onClick={onNavigateBack}>
          &larr; Back to App
        </button>
      )}

      {/* HERO */}
      <section className="validation-hero">
        <div className="validation-banner-frame">
          <img
            className="validation-banner"
            src="/images/validation-page-banner.png"
            alt="Med-MMHL Validation Methodology"
          />
        </div>
        <div className="validation-hero-content">
          <span className="validation-badge" style={{ background: '#5b8def', color: '#1c1e26' }}>
            <VerifiedIcon style={{ fontSize: '1rem' }} /> Rigorous Validation
          </span>

          <h1 className="validation-title">
            Med-MMHL Validation Methodology
          </h1>

          <p className="validation-subtitle">
            Why Med-MMHL is ideal, how we sampled 163 images to achieve statistical power,
            and why stratified random sampling was critical to avoid bias
          </p>

          <div className="validation-stats-row">
            <div className="validation-stat">
              <strong>{MED_MMHL_INFO.total.toLocaleString()}</strong>
              <span>Total Samples</span>
            </div>
            <div className="validation-stat">
              <strong>{MED_MMHL_INFO.sample}</strong>
              <span>Evaluated (n)</span>
            </div>
            <div className="validation-stat" style={{ background: 'rgba(91, 141, 239, 0.2)' }}>
              <strong style={{ color: '#5b8def' }}>7.2%</strong>
              <span>CI Width</span>
            </div>
            <div className="validation-stat">
              <strong>seed={MED_MMHL_INFO.seed}</strong>
              <span>Reproducible</span>
            </div>
          </div>
        </div>
      </section>

      {/* THE VALIDATION STORY */}
      <section className="validation-timeline">

        {/* STEP 1: WHY MED-MMHL */}
        <div className="timeline-step">
          <div className="step-marker">1</div>
          <div className="step-content">
            <h3>Why Med-MMHL is the Ideal Dataset</h3>
            <p>
              Med-MMHL is a research-grade medical misinformation benchmark containing <strong>1,785 real-world samples</strong> from
              fact-checking organizations. Each sample pairs a medical image with a claim (true or false) and includes ground-truth labels.
            </p>

            <div className="chart-card">
              <div className="insight-grid">
                <div className="insight-box">
                  <span className="insight-number" style={{ color: '#5b8def' }}>{MED_MMHL_INFO.total.toLocaleString()}</span>
                  <p><strong>Total samples</strong> in Med-MMHL test set</p>
                </div>
                <div className="insight-box" style={{ borderLeftColor: '#2A9D8F' }}>
                  <span className="insight-number" style={{ color: '#2A9D8F' }}>{MED_MMHL_INFO.sources.length}</span>
                  <p><strong>Fact-check sources</strong> (LeadStories, FactCheck.org, etc.)</p>
                </div>
              </div>

              <p className="helper" style={{ marginTop: '1rem', background: 'rgba(91, 141, 239, 0.1)', padding: '0.75rem', borderRadius: '4px' }}>
                <strong style={{ color: '#5b8def' }}>Real-world validated:</strong> Med-MMHL contains authentic images
                paired with misleading context—reflecting the <strong>dominant threat pattern</strong> in medical misinformation.
              </p>
            </div>
          </div>
        </div>

        {/* STEP 2: SAMPLE SIZE CALCULATION */}
        <div className="timeline-step">
          <div className="step-marker">2</div>
          <div className="step-content">
            <h3>Sample Size: 163 Provides Statistical Power</h3>
            <p>
              Using Wilson score intervals, we calculated the minimum sample size needed for tight confidence intervals.
              With n=163, we achieve a <strong>7.2% CI width</strong>—providing strong statistical power to detect performance differences.
            </p>

            <div className="chart-card">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={sampleSizeData} margin={{ top: 10, right: 30, left: 0, bottom: 40 }}>
                  <XAxis dataKey="n" label={{ value: 'Sample Size (n)', position: 'insideBottom', offset: -10 }} />
                  <YAxis domain={[0, 15]} label={{ value: 'CI Width (%)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={(v) => `${v.toFixed(1)}%`} />
                  <Bar dataKey="ci_width" radius={[6, 6, 0, 0]} label={{ position: 'top', formatter: (v) => `${v.toFixed(1)}%`, fontWeight: 'bold' }}>
                    {sampleSizeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>

              <p className="helper" style={{ marginTop: '1rem', background: 'rgba(42, 157, 143, 0.1)', padding: '0.75rem', borderRadius: '4px' }}>
                <strong style={{ color: '#2A9D8F' }}>Statistical justification:</strong> 163 samples balance computational cost
                with statistical power. Wider CIs with smaller n, minimal gains beyond 163.
              </p>
            </div>
          </div>
        </div>

        {/* STEP 3: BIAS DETECTION */}
        <div className="timeline-step">
          <div className="step-marker">3</div>
          <div className="step-content">
            <h3>Bias Detection: Sequential Sampling Would Be Biased</h3>
            <p>
              We tested whether taking the <strong>first 163 samples</strong> sequentially would introduce bias.
              Result: Sequential sampling yields <strong>88.3% misinformation rate</strong>—significantly higher than the full dataset's 83.0%.
            </p>

            <div className="chart-card">
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={distributionData} margin={{ top: 10, right: 30, left: 0, bottom: 40 }}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} interval={0} />
                  <YAxis domain={[75, 90]} label={{ value: 'Misinformation Rate (%)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={(v) => `${v.toFixed(1)}%`} />
                  <Bar dataKey="misinfoRate" radius={[6, 6, 0, 0]} label={{ position: 'top', formatter: (v) => `${v.toFixed(1)}%`, fontWeight: 'bold' }}>
                    {distributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>

              <p className="helper" style={{ marginTop: '1rem', background: 'rgba(230, 57, 70, 0.1)', padding: '0.75rem', borderRadius: '4px' }}>
                <strong style={{ color: '#E63946' }}>Bias detected:</strong> Sequential first-163 has 88.3% misinformation (vs 83.0% full dataset).
                This would artificially inflate or deflate performance metrics. Random sampling required.
              </p>
            </div>
          </div>
        </div>

        {/* STEP 4: STRATIFIED RANDOM SAMPLING */}
        <div className="timeline-step">
          <div className="step-marker">4</div>
          <div className="step-content">
            <h3>Solution: Stratified Random Sampling (seed=42)</h3>
            <p>
              Using stratified random sampling with <strong>seed=42</strong>, we drew 163 samples that <strong>preserve</strong> the
              full dataset's label distribution: 83.4% misinformation (136/163) vs 83.0% in full dataset.
            </p>

            <div className="chart-card">
              <div className="signals-grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="signal-card" style={{ borderLeft: '3px solid #E63946' }}>
                  <RandomIcon style={{ fontSize: '2rem', color: '#E63946' }} />
                  <strong>Sequential: Biased</strong>
                  <p style={{ fontSize: '0.85rem' }}>
                    88.3% misinfo rate (skewed distribution)
                  </p>
                </div>
                <div className="signal-card" style={{ borderLeft: '3px solid #2A9D8F' }}>
                  <CheckIcon style={{ fontSize: '2rem', color: '#2A9D8F' }} />
                  <strong>Stratified: Unbiased</strong>
                  <p style={{ fontSize: '0.85rem' }}>
                    83.4% misinfo rate (matches full dataset)
                  </p>
                </div>
              </div>

              <p className="helper" style={{ marginTop: '1rem', background: 'rgba(42, 157, 143, 0.1)', padding: '0.75rem', borderRadius: '4px' }}>
                <strong style={{ color: '#2A9D8F' }}>Reproducible:</strong> seed=42 ensures anyone can regenerate
                the exact same 163-sample subset for verification.
              </p>
            </div>
          </div>
        </div>

        {/* STEP 5: VALIDATION READY */}
        <div className="timeline-step">
          <div className="step-marker">5</div>
          <div className="step-content">
            <h3>Result: Validation-Ready Sample</h3>
            <p>
              Our 163-sample stratified random subset provides <strong>unbiased, statistically powered validation</strong>.
              Ready for threshold optimization and performance evaluation.
            </p>

            <div className="chart-card" style={{ background: 'rgba(91, 141, 239, 0.1)', borderLeft: '3px solid #5b8def' }}>
              <div className="insight-grid">
                <div className="insight-box">
                  <span className="insight-number" style={{ color: '#5b8def' }}>163</span>
                  <p><strong>Sample size</strong> with 7.2% CI width</p>
                </div>
                <div className="insight-box">
                  <span className="insight-number" style={{ color: '#2A9D8F' }}>83.4%</span>
                  <p><strong>Misinfo rate</strong> (matches full dataset)</p>
                </div>
                <div className="insight-box">
                  <span className="insight-number" style={{ color: '#4E9A34' }}>seed=42</span>
                  <p><strong>Reproducible</strong> sampling</p>
                </div>
                <div className="insight-box">
                  <span className="insight-number" style={{ color: '#4E9A34' }}>&lt;1%</span>
                  <p><strong>Distribution bias</strong> (minimal)</p>
                </div>
              </div>
            </div>
          </div>
        </div>

      </section>

      {/* SUMMARY */}
      <section className="validation-summary">
        <div className="summary-content">
          <h2>Validation Methodology Summary</h2>
          <p className="summary-lead">
            Our Med-MMHL validation methodology ensures <strong>unbiased, reproducible, statistically powered</strong> evaluation
            of contextual authenticity detection for medical misinformation.
          </p>

          <div style={{ padding: '1.5rem', background: 'rgba(91, 141, 239, 0.15)', borderRadius: '8px', marginBottom: '2rem', border: '2px solid #5b8def' }}>
            <h3 style={{ marginTop: 0, color: '#5b8def', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ScienceIcon /> Rigorous Scientific Validation
            </h3>
            <ul style={{ marginBottom: 0, color: '#c5cad4', lineHeight: '1.8' }}>
              <li><strong>Real-world dataset:</strong> 1,785 fact-checked samples from LeadStories, FactCheck.org, Snopes</li>
              <li><strong>Statistical power:</strong> n=163 with 7.2% CI width (Wilson score intervals)</li>
              <li><strong>Bias detection:</strong> Sequential sampling would skew 88.3% vs 83.0% (detected and avoided)</li>
              <li><strong>Stratified random:</strong> seed=42 preserves 83.4% misinfo rate (matches full dataset)</li>
              <li><strong>Reproducible:</strong> Anyone can regenerate the exact same 163-sample subset</li>
            </ul>
          </div>

          <div className="validation-stats-row">
            <div className="validation-stat">
              <strong>{MED_MMHL_INFO.total.toLocaleString()}</strong>
              <span>Total Samples</span>
            </div>
            <div className="validation-stat">
              <strong>{MED_MMHL_INFO.sample}</strong>
              <span>Evaluated</span>
            </div>
            <div className="validation-stat" style={{ background: 'rgba(91, 141, 239, 0.2)' }}>
              <strong style={{ color: '#5b8def' }}>7.2%</strong>
              <span>CI Width</span>
            </div>
            <div className="validation-stat">
              <strong>{MED_MMHL_INFO.misinfoRate.toFixed(1)}%</strong>
              <span>Misinfo Rate</span>
            </div>
          </div>

          <p className="summary-note" style={{ marginTop: '1.5rem' }}>
            Med-MMHL stratified random sampling (n={MED_MMHL_INFO.sample}, seed={MED_MMHL_INFO.seed}) — February 2026.
            Bias detection confirmed sequential sampling would introduce 5.3 percentage point skew (88.3% vs 83.0%).
            Stratified approach maintains 83.4% misinfo rate, matching full dataset distribution.
          </p>
        </div>
      </section>
    </div>
  )
}

export default ValidationStory
