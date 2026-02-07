import {
  Psychology as BrainIcon,
  CheckCircle as CheckIcon,
  HourglassEmpty as PendingIcon,
  Rocket as RocketIcon,
  Shield as ShieldIcon,
  TrackChanges as TargetIcon,
  Warning as WarningIcon
} from '@mui/icons-material'
import { useMemo } from 'react'
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts'
import './ValidationStory.css'

// Three-dimensional validation data — per-dimension accuracy
// Populated from validation_results/three_method_v1/three_method_comparison.json (Feb 7, 2026)
const VALIDATION_DATA = {
  dimensions: {
    integrity: { exact_match: 0.250, binary_accuracy: 0.250, binary_f1: 0.0, n: 160 },
    veracity: { exact_match: 0.594, binary_accuracy: 0.619, binary_f1: 0.591, n: 160 },
    alignment: { exact_match: 0.556, binary_accuracy: 0.606, binary_f1: 0.540, n: 160 },
  },
  score_distribution: { '0/3': 33, '1/3': 39, '2/3': 79, '3/3': 9 },
  category_analysis: {
    legitimate: { integrity: 0.0, veracity: 0.933, alignment: 0.933, count: 30 },
    misleading: { integrity: 0.0, veracity: 0.233, alignment: 0.700, count: 30 },
    intentional_misinfo: { integrity: 0.0, veracity: 0.967, alignment: 0.967, count: 30 },
    other_authentic: { integrity: 0.0, veracity: 0.100, alignment: 0.067, count: 30 },
    tampered: { integrity: 1.0, veracity: 0.675, alignment: 0.225, count: 40 },
  },
  dataset: {
    total: 160,
    available: 160,
    unique_images: 110,
    pixel_authentic: 120,
    pixel_tampered: 40,
  },
}

const fmt = (v, decimals = 1) =>
  v !== null && v !== undefined ? `${(v * 100).toFixed(decimals)}%` : '\u2014'

function ValidationStory({ onNavigateBack }) {
  const isPending = VALIDATION_DATA.dimensions.integrity.binary_accuracy === null

  const dimensionData = useMemo(
    () => [
      {
        name: 'Image\nIntegrity',
        accuracy: VALIDATION_DATA.dimensions.integrity.binary_accuracy !== null
          ? VALIDATION_DATA.dimensions.integrity.binary_accuracy * 100
          : 0,
        fill: '#4E9A34',
        label: fmt(VALIDATION_DATA.dimensions.integrity.binary_accuracy),
      },
      {
        name: 'Claim\nVeracity',
        accuracy: VALIDATION_DATA.dimensions.veracity.binary_accuracy !== null
          ? VALIDATION_DATA.dimensions.veracity.binary_accuracy * 100
          : 0,
        fill: '#2db88a',
        label: fmt(VALIDATION_DATA.dimensions.veracity.binary_accuracy),
      },
      {
        name: 'Context\nAlignment',
        accuracy: VALIDATION_DATA.dimensions.alignment.binary_accuracy !== null
          ? VALIDATION_DATA.dimensions.alignment.binary_accuracy * 100
          : 0,
        fill: '#5b8def',
        label: fmt(VALIDATION_DATA.dimensions.alignment.binary_accuracy),
      },
    ],
    [],
  )

  const datasetData = useMemo(
    () => [
      { name: 'Legitimate', value: 30, fill: '#2db88a' },
      { name: 'Misleading context', value: 30, fill: '#f5a524' },
      { name: 'Intentional misinfo', value: 30, fill: '#e5484d' },
      { name: 'Other authentic', value: 30, fill: '#6d7d93' },
      { name: 'Tampered (DICOM)', value: 40, fill: '#a855f7' },
    ],
    [],
  )

  const categoryData = useMemo(() => {
    const categories = VALIDATION_DATA.category_analysis
    return Object.entries(categories)
      .filter(([, v]) => v.veracity !== null)
      .map(([key, v]) => ({
        name: key.replace(/_/g, ' '),
        integrity: v.integrity !== null ? v.integrity * 100 : 0,
        veracity: v.veracity !== null ? v.veracity * 100 : 0,
        alignment: v.alignment !== null ? v.alignment * 100 : 0,
        count: v.count,
      }))
  }, [])

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
            Three-Dimensional Validation
          </h1>
          <p className="validation-subtitle">
            Scoring image integrity, claim veracity, and context alignment independently across
            160 image-claim pairs to reveal where detection succeeds and fails
          </p>
          <div className="validation-stats-row">
            <div className="validation-stat">
              <strong>{isPending ? '\u2014' : fmt(VALIDATION_DATA.dimensions.integrity.binary_accuracy, 1)}</strong>
              <span>Integrity (ELA)</span>
            </div>
            <div className="validation-stat">
              <strong>{isPending ? '\u2014' : fmt(VALIDATION_DATA.dimensions.veracity.binary_accuracy, 1)}</strong>
              <span>Veracity (MedGemma)</span>
            </div>
            <div className="validation-stat">
              <strong>{isPending ? '\u2014' : fmt(VALIDATION_DATA.dimensions.alignment.binary_accuracy, 1)}</strong>
              <span>Alignment (MedGemma)</span>
            </div>
            <div className="validation-stat">
              <strong>160</strong>
              <span>Image-Claim Pairs</span>
            </div>
          </div>

          {isPending ? (
            <p style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(245, 165, 36, 0.1)', borderRadius: '8px', borderLeft: '3px solid #f5a524', fontSize: '0.9rem', lineHeight: '1.6', color: '#c5cad4' }}>
              <strong style={{ color: '#f5a524', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                <PendingIcon style={{ fontSize: '1rem' }} /> Processing:
              </strong>{' '}
              Running three-dimensional validation on 160 image-claim pairs. Each sample is scored on
              integrity (ELA), veracity (MedGemma), and alignment (MedGemma).
              Results will appear here when the run completes.
            </p>
          ) : (
            <p style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(45, 184, 138, 0.1)', borderRadius: '8px', borderLeft: '3px solid #2db88a', fontSize: '0.9rem', lineHeight: '1.6', color: '#c5cad4' }}>
              <strong style={{ color: '#2db88a', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
                <CheckIcon style={{ fontSize: '1rem' }} /> Validation Complete:
              </strong>{' '}
              All 160 image-claim pairs scored across three dimensions.
              Integrity: {fmt(VALIDATION_DATA.dimensions.integrity.binary_accuracy)},
              Veracity: {fmt(VALIDATION_DATA.dimensions.veracity.binary_accuracy)},
              Alignment: {fmt(VALIDATION_DATA.dimensions.alignment.binary_accuracy)}.
            </p>
          )}
        </div>
      </section>

      {/* Story Timeline */}
      <section className="validation-timeline">
        <div className="timeline-header">
          <h2>The Validation Story</h2>
          <p className="helper">Why misinformation detection needs three dimensions, not one</p>
        </div>

        {/* Step 1: The Problem */}
        <div className="timeline-step">
          <div className="step-marker">1</div>
          <div className="step-content">
            <h3>The Problem: Misinformation Is Multidimensional</h3>
            <p>
              Medical misinformation is not just about fake images or false claims in isolation.
              It occurs at the <strong>intersection of three independent dimensions</strong>: whether the image
              is authentic, whether the claim is true, and whether they actually belong together.
              Any single-axis detector misses the other two.
            </p>
            <div className="chart-card">
              <h4>Why Single-Axis Detection Fails</h4>
              <div className="insight-grid">
                <div className="insight-box">
                  <span className="insight-number">75%</span>
                  <p>of samples in our dataset use <strong>authentic images</strong> &mdash; pixel forensics returns no signal for these</p>
                </div>
                <div className="insight-box" style={{ borderLeftColor: '#e5484d' }}>
                  <span className="insight-number" style={{ color: '#e5484d' }}>8</span>
                  <p>distinct misinformation categories emerge from the <strong>2&times;2&times;2</strong> combination of three binary dimensions</p>
                </div>
              </div>
              <p className="helper" style={{ marginTop: '1rem', background: 'rgba(91, 141, 239, 0.1)', padding: '0.75rem', borderRadius: '4px', color: '#c5cad4' }}>
                <strong style={{ color: '#5b8def' }}>Key insight:</strong>{' '}
                The most dangerous category &mdash; an authentic image aligned with a false claim &mdash; is
                invisible to pixel forensics and undetectable by claim fact-checking alone.
                Only by assessing all three dimensions together can we identify it.
              </p>
            </div>
          </div>
        </div>

        {/* Step 2: The Three Dimensions */}
        <div className="timeline-step">
          <div className="step-marker">2</div>
          <div className="step-content">
            <h3>The Framework: Three Dimensions of Authenticity</h3>
            <p>
              MedContext evaluates each image-claim pair across three independent dimensions,
              forming a triangle of assessment. Each dimension can pass, fail, or be partially met.
            </p>
            <div className="chart-card">
              <h4>The Three Dimensions</h4>
              <div className="signals-grid">
                <div className="signal-card" style={{ borderLeft: '3px solid #4E9A34' }}>
                  <span className="signal-icon"><ShieldIcon style={{ fontSize: '2rem', color: '#4E9A34' }} /></span>
                  <strong>Image Integrity</strong>
                  <p>Is the image itself authentic and unmodified? Detects pixel-level tampering.</p>
                  <small style={{ color: '#9ba0af' }}>Pixel forensics, ELA, metadata checks</small>
                </div>
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
            </div>
          </div>
        </div>

        {/* Step 3: The 2x2x2 Matrix */}
        <div className="timeline-step">
          <div className="step-marker">3</div>
          <div className="step-content">
            <h3>The 2&times;2&times;2 Matrix: Eight Possible States</h3>
            <p>
              Crossing the three binary dimensions produces 8 distinct states. Each represents
              a different type of content &mdash; from fully verified to maximally deceptive.
            </p>
            <div className="chart-card">
              <h4>All 8 Categories in the Validation Dataset</h4>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '1rem' }}>
                {[
                  { label: 'Verified context', desc: 'Authentic + true + aligned', tone: '#2db88a', key: 'PPP' },
                  { label: 'True claim, wrong image', desc: 'Authentic + true + misaligned', tone: '#f5a524', key: 'PPF' },
                  { label: 'Image supports false claim', desc: 'Authentic + false + aligned', tone: '#e5484d', key: 'PFP' },
                  { label: 'False claim, wrong image', desc: 'Authentic + false + misaligned', tone: '#6d7d93', key: 'PFF' },
                  { label: 'Tampered but aligned', desc: 'Tampered + true + aligned', tone: '#f5a524', key: 'FPP' },
                  { label: 'Tampered, mismatched', desc: 'Tampered + true + misaligned', tone: '#6d7d93', key: 'FPF' },
                  { label: 'Tampered supports false claim', desc: 'Tampered + false + aligned', tone: '#e5484d', key: 'FFP' },
                  { label: 'All signals fail', desc: 'Tampered + false + misaligned', tone: '#6d7d93', key: 'FFF' },
                ].map(cell => (
                  <div key={cell.key} style={{
                    padding: '0.75rem',
                    borderRadius: '6px',
                    borderLeft: `3px solid ${cell.tone}`,
                    background: 'rgba(255,255,255,0.03)',
                  }}>
                    <strong style={{ color: '#e9eef4', fontSize: '0.85rem', display: 'block' }}>{cell.label}</strong>
                    <small style={{ color: '#9ba0af' }}>{cell.desc}</small>
                  </div>
                ))}
              </div>
              <p className="helper" style={{ marginTop: '1rem', color: '#c5cad4' }}>
                <strong style={{ color: '#e5484d' }}>Most dangerous:</strong>{' '}
                &ldquo;Image supports false claim&rdquo; (authentic + false + aligned) &mdash; a real image
                used to lend credibility to a false claim. Only the combined approach can detect this.
              </p>
            </div>
          </div>
        </div>

        {/* Step 4: The Dataset */}
        <div className="timeline-step">
          <div className="step-marker">4</div>
          <div className="step-content">
            <h3>The Dataset: 160 Samples Across 5 Categories</h3>
            <p>
              We created a validation dataset combining 120 authentic MRI image-claim pairs from the BTD
              (Brain Tumor Detection) dataset with 40 tampered medical scans from the UCI Medical Image
              Tamper Detection dataset, generating 160 samples across 5 categories. The authentic images
              test contextual analysis; the tampered images test pixel forensics.
            </p>
            <div className="chart-card">
              <h4>Dataset Composition</h4>
              <div className="viz-row">
                <div className="viz-col">
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={datasetData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        label={({ value }) => value}
                      >
                        {datasetData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="viz-col">
                  <ul className="dataset-list">
                    <li>
                      <span className="list-dot" style={{ background: '#2db88a' }} />
                      <strong>30 Legitimate:</strong> Authentic image, true claim, aligned (3/3)
                    </li>
                    <li>
                      <span className="list-dot" style={{ background: '#f5a524' }} />
                      <strong>30 Misleading:</strong> Authentic image, true claim, misaligned (2/3)
                    </li>
                    <li>
                      <span className="list-dot" style={{ background: '#e5484d' }} />
                      <strong>30 Intentional misinfo:</strong> Authentic image, false claim, misaligned (1/3)
                    </li>
                    <li>
                      <span className="list-dot" style={{ background: '#6d7d93' }} />
                      <strong>30 Other authentic:</strong> Authentic image, partial veracity, partial alignment (1/3)
                    </li>
                    <li>
                      <span className="list-dot" style={{ background: '#a855f7' }} />
                      <strong>40 Tampered:</strong> UCI tampered DICOM scans with varied claims (tests pixel forensics)
                    </li>
                  </ul>
                </div>
              </div>
              <div className="insight-grid" style={{ marginTop: '1rem' }}>
                <div className="insight-box" style={{ borderLeftColor: '#4E9A34' }}>
                  <span className="insight-number" style={{ color: '#4E9A34' }}>75%</span>
                  <p>of images are <strong>authentic MRIs</strong> (120/160) &mdash; 40 are tampered DICOM scans for pixel forensics testing</p>
                </div>
                <div className="insight-box" style={{ borderLeftColor: '#e5484d' }}>
                  <span className="insight-number" style={{ color: '#e5484d' }}>50%</span>
                  <p>of samples have <strong>misaligned or false claims</strong>, requiring contextual analysis to detect</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Step 5: How Each Dimension Is Assessed */}
        <div className="timeline-step">
          <div className="step-marker">5</div>
          <div className="step-content">
            <h3>How Each Dimension Is Assessed</h3>
            <p>
              Each of the 160 samples is scored independently on all three dimensions.
              Each dimension uses the method best suited to it.
            </p>
            <div className="chart-card">
              <h4>Assessment Methods</h4>
              <div className="signals-grid">
                <div className="signal-card" style={{ borderLeft: '3px solid #4E9A34' }}>
                  <span className="signal-icon"><ShieldIcon style={{ fontSize: '2rem', color: '#4E9A34' }} /></span>
                  <strong>Image Integrity</strong>
                  <p>Error Level Analysis (ELA) detects pixel-level tampering
                  by comparing JPEG compression artifacts.</p>
                  <small style={{ color: '#4E9A34', fontWeight: 'bold' }}>Scored 1/3 (fail) to 3/3 (pass)</small>
                </div>
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
            <h3>Results: Per-Dimension Accuracy</h3>
            {isPending ? (
              <div style={{ padding: '2rem', background: 'rgba(245, 165, 36, 0.08)', borderRadius: '12px', border: '2px dashed #f5a524', textAlign: 'center' }}>
                <PendingIcon style={{ fontSize: '3rem', color: '#f5a524', marginBottom: '1rem' }} />
                <h4 style={{ color: '#f5a524', marginBottom: '0.5rem' }}>Validation Running</h4>
                <p style={{ color: '#9ba0af', maxWidth: '500px', margin: '0 auto', lineHeight: '1.6' }}>
                  Processing 160 image-claim pairs. Each sample scored on
                  integrity (ELA), veracity (MedGemma), and alignment (MedGemma).
                  Results will populate when the run completes.
                </p>
              </div>
            ) : (
              <>
                <p>
                  All 160 image-claim pairs scored across three dimensions.
                  Integrity (ELA): {fmt(VALIDATION_DATA.dimensions.integrity.binary_accuracy)},
                  Veracity: {fmt(VALIDATION_DATA.dimensions.veracity.binary_accuracy)},
                  Alignment: {fmt(VALIDATION_DATA.dimensions.alignment.binary_accuracy)}.
                </p>
                <div className="chart-card">
                  <h4>Per-Dimension Accuracy</h4>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={dimensionData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                      <XAxis dataKey="name" angle={0} textAnchor="middle" height={60} />
                      <YAxis domain={[0, 100]} label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }} />
                      <Tooltip
                        formatter={(value) => `${value.toFixed(1)}%`}
                        contentStyle={{ background: '#1c1e26', border: '1px solid #2d3142' }}
                      />
                      <Bar dataKey="accuracy" radius={[8, 8, 0, 0]}>
                        {dimensionData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.fill} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Detailed metrics table */}
                <div className="chart-card" style={{ marginTop: '1rem' }}>
                  <h4>Detailed Metrics by Dimension</h4>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                      <thead>
                        <tr style={{ borderBottom: '2px solid #2d3142' }}>
                          <th style={{ textAlign: 'left', padding: '0.75rem', color: '#9ba0af' }}>Dimension</th>
                          <th style={{ textAlign: 'right', padding: '0.75rem', color: '#9ba0af' }}>Exact Match</th>
                          <th style={{ textAlign: 'right', padding: '0.75rem', color: '#9ba0af' }}>Accuracy</th>
                          <th style={{ textAlign: 'right', padding: '0.75rem', color: '#9ba0af' }}>F1</th>
                          <th style={{ textAlign: 'right', padding: '0.75rem', color: '#9ba0af' }}>n</th>
                        </tr>
                      </thead>
                      <tbody>
                        {[
                          { key: 'integrity', label: 'Image Integrity (ELA)', color: '#4E9A34' },
                          { key: 'veracity', label: 'Claim Veracity', color: '#2db88a' },
                          { key: 'alignment', label: 'Context Alignment', color: '#5b8def' },
                        ].map(({ key, label, color }) => {
                          const m = VALIDATION_DATA.dimensions[key]
                          return (
                            <tr key={key} style={{ borderBottom: '1px solid #2d3142' }}>
                              <td style={{ padding: '0.75rem', color, fontWeight: 600 }}>{label}</td>
                              <td style={{ textAlign: 'right', padding: '0.75rem', color: '#c5cad4' }}>{fmt(m.exact_match)}</td>
                              <td style={{ textAlign: 'right', padding: '0.75rem', color: '#c5cad4' }}>{fmt(m.binary_accuracy)}</td>
                              <td style={{ textAlign: 'right', padding: '0.75rem', color: '#c5cad4' }}>{fmt(m.binary_f1)}</td>
                              <td style={{ textAlign: 'right', padding: '0.75rem', color: '#c5cad4' }}>{m.n}</td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Step 7: Per-Category Analysis */}
        <div className="timeline-step">
          <div className="step-marker">7</div>
          <div className="step-content">
            <h3>Where Each Dimension Excels (and Fails)</h3>
            <p>
              The real test is per-category performance. Integrity (ELA) should score uniformly
              since all images are authentic. Veracity and alignment should differentiate
              between legitimate, misleading, and misinformation categories.
            </p>
            {isPending ? (
              <div className="chart-card" style={{ textAlign: 'center', padding: '2rem', color: '#9ba0af' }}>
                <PendingIcon style={{ fontSize: '2rem', color: '#f5a524' }} />
                <p>Per-category breakdowns will appear after validation completes.</p>
              </div>
            ) : categoryData.length > 0 ? (
              <div className="chart-card">
                <h4>Accuracy by Category and Dimension</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={categoryData} layout="vertical" margin={{ left: 30, right: 20 }}>
                    <XAxis type="number" domain={[0, 100]} />
                    <YAxis type="category" dataKey="name" width={160} style={{ fontSize: '0.8rem' }} />
                    <Tooltip
                      formatter={(value) => `${value.toFixed(1)}%`}
                      contentStyle={{ background: '#1c1e26', border: '1px solid #2d3142' }}
                    />
                    <Bar dataKey="integrity" name="Integrity (ELA)" fill="#4E9A34" />
                    <Bar dataKey="veracity" name="Veracity" fill="#2db88a" />
                    <Bar dataKey="alignment" name="Alignment" fill="#5b8def" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : null}
            <div className="chart-card" style={{ marginTop: '1rem' }}>
              <h4>Expected Patterns</h4>
              <div className="insight-grid">
                <div className="insight-box" style={{ borderLeftColor: '#4E9A34' }}>
                  <span className="insight-number" style={{ color: '#4E9A34', fontSize: '1.5rem' }}>Integrity</span>
                  <p>ELA predicts MANIPULATED for all MRI images due to high compression variance &mdash; a <strong>degenerate predictor</strong> for this domain</p>
                </div>
                <div className="insight-box" style={{ borderLeftColor: '#2db88a' }}>
                  <span className="insight-number" style={{ color: '#2db88a', fontSize: '1.5rem' }}>Veracity</span>
                  <p>MedGemma should correctly identify <strong>false claims</strong> (intentional misinfo) while recognizing true claims (legitimate, misleading)</p>
                </div>
                <div className="insight-box" style={{ borderLeftColor: '#5b8def' }}>
                  <span className="insight-number" style={{ color: '#5b8def', fontSize: '1.5rem' }}>Alignment</span>
                  <p>MedGemma should detect when <strong>true claims don&rsquo;t match the image</strong> &mdash; the hardest category (misleading)</p>
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
                  <li>Medical misinformation requires <strong>three-dimensional</strong> assessment &mdash; no single axis is sufficient</li>
                  <li>ELA is a degenerate predictor for medical imaging &mdash; high compression variance makes all MRIs look &ldquo;manipulated&rdquo;</li>
                  <li>Contextual analysis (veracity + alignment) covers what pixel forensics cannot</li>
                  {isPending ? (
                    <li>Quantitative per-dimension results pending completion of 160-sample run</li>
                  ) : (
                    <>
                      <li>Integrity: <strong>{fmt(VALIDATION_DATA.dimensions.integrity.binary_accuracy)}</strong>,
                        Veracity: <strong>{fmt(VALIDATION_DATA.dimensions.veracity.binary_accuracy)}</strong>,
                        Alignment: <strong>{fmt(VALIDATION_DATA.dimensions.alignment.binary_accuracy)}</strong></li>
                    </>
                  )}
                </ul>
              </div>

              <div className="conclusion-card conclusion-caution">
                <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <WarningIcon /> Known Limitations
                </h4>
                <ul>
                  <li><strong>Pixel forensics baseline:</strong> ELA is known to fail on medical imaging due to inherent compression variance</li>
                  <li><strong>Contextual analysis:</strong> Uses direct MedGemma inference without full agent orchestration</li>
                  <li>Dataset limited to brain MRI images from BTD &mdash; may not generalize to other modalities</li>
                  <li>Ground truth labels are synthetically assigned, not expert-annotated</li>
                  <li>40 tampered images are DICOM (UCI dataset) &mdash; different modality from BTD MRI PNGs</li>
                  <li>160 samples provides moderate statistical power; 500+ would be stronger</li>
                </ul>
              </div>

              <div className="conclusion-card conclusion-future">
                <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <RocketIcon /> Next Steps
                </h4>
                <ul>
                  <li>Scale to 500+ samples across diverse medical imaging modalities (X-ray, CT, histopathology)</li>
                  <li>Replace ELA with learned pixel forensics (deep learning tampering detection)</li>
                  <li>Add provenance and reverse search signals for full 5-dimension assessment</li>
                  <li>Expert annotation of ground truth labels</li>
                  <li>Field deployment validation with HERO Lab, UBC</li>
                  <li>Compare against human expert baseline</li>
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
                Medical misinformation operates across three dimensions: image integrity, claim veracity,
                and context-image alignment. Each dimension is scored independently (0/3 to 3/3),
                revealing exactly where detection succeeds and fails.
              </p>
              <div style={{ padding: '1.5rem', background: 'rgba(245, 165, 36, 0.15)', borderRadius: '8px', marginBottom: '2rem', border: '2px solid #f5a524' }}>
                <h3 style={{ marginTop: 0, color: '#f5a524', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <PendingIcon /> Awaiting Results
                </h3>
                <p style={{ marginBottom: '0.5rem', color: '#c5cad4' }}>
                  <strong style={{ color: '#e9eef4' }}>Three dimensions, one dataset:</strong>{' '}
                  Each of 160 image-claim pairs is scored on integrity (ELA),
                  veracity (MedGemma), and alignment (MedGemma).
                </p>
                <p style={{ marginBottom: 0, color: '#c5cad4' }}>
                  <strong style={{ color: '#e9eef4' }}>Why this matters:</strong>{' '}
                  Per-dimension scoring reveals which aspects of misinformation detection
                  work and which need improvement &mdash; rather than collapsing to a single binary.
                </p>
              </div>
            </>
          ) : (
            <>
              <p className="summary-lead">
                Per-dimension accuracy: Integrity (ELA){' '}
                <strong>{fmt(VALIDATION_DATA.dimensions.integrity.binary_accuracy)}</strong>,
                Veracity{' '}
                <strong>{fmt(VALIDATION_DATA.dimensions.veracity.binary_accuracy)}</strong>,
                Alignment{' '}
                <strong>{fmt(VALIDATION_DATA.dimensions.alignment.binary_accuracy)}</strong>.
                ELA fails as expected on medical imaging. Contextual analysis provides
                the signal that pixel forensics cannot.
              </p>
              <div style={{ padding: '1.5rem', background: 'rgba(45, 184, 138, 0.15)', borderRadius: '8px', marginBottom: '2rem', border: '2px solid #2db88a' }}>
                <h3 style={{ marginTop: 0, color: '#2db88a', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <CheckIcon /> Validated
                </h3>
                <p style={{ marginBottom: 0, color: '#c5cad4' }}>
                  Three-dimensional scoring reveals that contextual analysis (veracity + alignment)
                  is the critical capability for medical misinformation detection, while pixel forensics
                  alone is insufficient for this domain.
                </p>
              </div>
            </>
          )}
          <div className="summary-stats">
            <div className="summary-stat-large">
              <span className="stat-value">{isPending ? '\u2014' : fmt(VALIDATION_DATA.dimensions.veracity.binary_accuracy, 1)}</span>
              <span className="stat-label">Veracity Accuracy</span>
            </div>
            <div className="summary-stat-large">
              <span className="stat-value">{isPending ? '\u2014' : fmt(VALIDATION_DATA.dimensions.alignment.binary_accuracy, 1)}</span>
              <span className="stat-label">Alignment Accuracy</span>
            </div>
            <div className="summary-stat-large">
              <span className="stat-value">160</span>
              <span className="stat-label">Image-Claim Pairs</span>
            </div>
            <div className="summary-stat-large">
              <span className="stat-value">3</span>
              <span className="stat-label">Dimensions Scored</span>
            </div>
          </div>
          <p className="summary-note">
            Three-dimensional validation &mdash; 160 image-claim pairs from BTD and UCI medical imaging datasets.
            120 authentic MRIs + 40 tampered DICOM scans, paired with claims of varying veracity and alignment.
            Integrity via ELA, veracity and alignment via direct MedGemma inference.
          </p>
        </div>
      </section>
    </div>
  )
}

export default ValidationStory
