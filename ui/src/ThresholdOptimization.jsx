import { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ScatterChart, Scatter, ZAxis, Legend } from 'recharts'
import './App.css'

export default function ThresholdOptimization({ apiBase, accessCode }) {
  const [datasetFile, setDatasetFile] = useState(null)
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')
  const [results, setResults] = useState(null)

  const handleFileChange = (e) => {
    const file = e.target.files?.[0]
    if (file) {
      setDatasetFile(file)
      setError('')
      setResults(null)
    }
  }

  const handleOptimize = async () => {
    if (!datasetFile) {
      setError('Please upload a dataset file')
      return
    }

    setStatus('running')
    setError('')
    setResults(null)

    try {
      const formData = new FormData()
      formData.append('dataset', datasetFile)

      const headers = {}
      if (accessCode?.trim()) {
        headers['X-Demo-Access-Code'] = accessCode.trim()
      }

      const res = await fetch(
        `${apiBase.replace(/\/$/, '')}/api/v1/orchestrator/optimize-thresholds`,
        {
          method: 'POST',
          headers,
          body: formData,
        }
      )

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errorData.detail || `HTTP ${res.status}`)
      }

      const data = await res.json()
      setResults(data)
      setStatus('complete')
    } catch (err) {
      setError(err.message)
      setStatus('error')
    }
  }

  const handleReset = () => {
    setDatasetFile(null)
    setStatus('idle')
    setError('')
    setResults(null)
  }

  return (
    <div className="threshold-optimization-container">
      <section className="card">
        <h2>Threshold Optimization</h2>
        <p className="helper" style={{ marginBottom: '1.5rem' }}>
          Optimal decision thresholds are model-specific and domain-specific. Upload a labeled validation dataset
          (JSON format with image-claim pairs and ground truth labels) to find the best thresholds for your use case.
        </p>

        <div className="insight-box" style={{ marginBottom: '1.5rem', borderLeftColor: '#f5a524' }}>
          <h4 style={{ color: '#f5a524', marginTop: 0 }}>Why Optimize Thresholds?</h4>
          <p style={{ fontSize: '0.9rem', lineHeight: '1.6', marginBottom: '0.5rem' }}>
            Our validation found that MedGemma 27B and 4B converge to <strong>identical optimal thresholds</strong> (veracity &lt; 0.65 OR alignment &lt; 0.30)
            but use them <strong>very differently</strong>:
          </p>
          <ul style={{ fontSize: '0.85rem', lineHeight: '1.6', marginLeft: '1.2rem' }}>
            <li><strong>27B:</strong> 95.0% precision, 98.5% recall (alignment-driven, high recall for health safety)</li>
            <li><strong>4B:</strong> 99.2% precision, 89.7% recall (veracity-driven, ultra-conservative)</li>
          </ul>
          <p style={{ fontSize: '0.9rem', lineHeight: '1.6', marginTop: '0.5rem' }}>
            Your model, domain, and risk tolerance may require different thresholds. Run this tool on a representative
            sample to find your optimal configuration.
          </p>
        </div>

        <div className="form-section">
          <h3>Upload Dataset</h3>
          <div className="file-upload-zone">
            <input
              type="file"
              accept=".json"
              onChange={handleFileChange}
              disabled={status === 'running'}
              id="dataset-upload"
              style={{ display: 'none' }}
            />
            <label htmlFor="dataset-upload" className="file-upload-label">
              {datasetFile ? (
                <>
                  <span style={{ color: '#2db88a' }}>✓</span> {datasetFile.name}
                </>
              ) : (
                <>📁 Choose Dataset File (.json)</>
              )}
            </label>
          </div>

          <details style={{ marginTop: '1rem', fontSize: '0.85rem', color: '#9ba0af' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 600 }}>Expected JSON Format</summary>
            <pre style={{ background: '#1c1e26', padding: '1rem', borderRadius: '8px', overflowX: 'auto', marginTop: '0.5rem' }}>
{`[
  {
    "image_path": "/path/to/image1.jpg",
    "claim": "This MRI shows...",
    "label": "misinformation"  // or "legitimate"
  },
  {
    "image_path": "/path/to/image2.jpg",
    "claim": "This scan indicates...",
    "label": "legitimate"
  }
]`}
            </pre>
          </details>

          {error && (
            <div className="error-message" style={{ marginTop: '1rem' }}>
              {error}
            </div>
          )}

          <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
            <button
              onClick={handleOptimize}
              disabled={!datasetFile || status === 'running'}
              className="submit-button"
              style={{ flex: 1 }}
            >
              {status === 'running' ? '⏳ Optimizing...' : '🔍 Find Optimal Thresholds'}
            </button>
            {(datasetFile || results) && (
              <button
                onClick={handleReset}
                disabled={status === 'running'}
                className="reset-button"
              >
                Reset
              </button>
            )}
          </div>
        </div>
      </section>

      {status === 'running' && (
        <section className="card" style={{ marginTop: '1.5rem' }}>
          <div style={{ padding: '2rem', textAlign: 'center' }}>
            <div className="spinner" style={{ margin: '0 auto 1rem' }}></div>
            <h3 style={{ color: '#f5a524', marginBottom: '0.5rem' }}>Running Threshold Optimization</h3>
            <p className="helper">
              Testing 363 threshold combinations (11 veracity × 11 alignment × 3 logics)...
              <br />
              This may take 2-5 minutes depending on dataset size.
            </p>
          </div>
        </section>
      )}

      {results && status === 'complete' && (
        <>
          <section className="card" style={{ marginTop: '1.5rem' }}>
            <h3>Optimal Configuration</h3>
            <div className="insight-grid" style={{ marginTop: '1rem' }}>
              <div className="insight-box" style={{ borderLeftColor: '#2db88a' }}>
                <span className="insight-number" style={{ color: '#2db88a' }}>
                  {results.optimal.logic}
                </span>
                <p><strong>Decision Logic</strong></p>
              </div>
              <div className="insight-box" style={{ borderLeftColor: '#5b8def' }}>
                <span className="insight-number" style={{ color: '#5b8def' }}>
                  {results.optimal.veracity_threshold.toFixed(2)}
                </span>
                <p><strong>Veracity Threshold</strong></p>
              </div>
              <div className="insight-box" style={{ borderLeftColor: '#e5484d' }}>
                <span className="insight-number" style={{ color: '#e5484d' }}>
                  {results.optimal.alignment_threshold.toFixed(2)}
                </span>
                <p><strong>Alignment Threshold</strong></p>
              </div>
            </div>

            <div className="chart-card" style={{ marginTop: '1.5rem' }}>
              <h4>Performance Metrics</h4>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #2d3142' }}>
                    <th style={{ padding: '0.75rem', textAlign: 'left' }}>Metric</th>
                    <th style={{ padding: '0.75rem', textAlign: 'right' }}>Value</th>
                    <th style={{ padding: '0.75rem', textAlign: 'right' }}>95% CI</th>
                  </tr>
                </thead>
                <tbody>
                  <tr style={{ borderBottom: '1px solid #2d3142' }}>
                    <td style={{ padding: '0.75rem' }}>Accuracy</td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 600 }}>
                      {(results.optimal.accuracy * 100).toFixed(1)}%
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontSize: '0.85rem', color: '#9ba0af' }}>
                      [{(results.bootstrap_ci.accuracy.ci_lower * 100).toFixed(1)}%, {(results.bootstrap_ci.accuracy.ci_upper * 100).toFixed(1)}%]
                    </td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid #2d3142' }}>
                    <td style={{ padding: '0.75rem' }}>Precision</td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 600 }}>
                      {(results.optimal.precision * 100).toFixed(1)}%
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontSize: '0.85rem', color: '#9ba0af' }}>
                      [{(results.bootstrap_ci.precision.ci_lower * 100).toFixed(1)}%, {(results.bootstrap_ci.precision.ci_upper * 100).toFixed(1)}%]
                    </td>
                  </tr>
                  <tr style={{ borderBottom: '1px solid #2d3142' }}>
                    <td style={{ padding: '0.75rem' }}>Recall</td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 600 }}>
                      {(results.optimal.recall * 100).toFixed(1)}%
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontSize: '0.85rem', color: '#9ba0af' }}>
                      [{(results.bootstrap_ci.recall.ci_lower * 100).toFixed(1)}%, {(results.bootstrap_ci.recall.ci_upper * 100).toFixed(1)}%]
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '0.75rem' }}>F1 Score</td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 600 }}>
                      {results.optimal.f1.toFixed(3)}
                    </td>
                    <td style={{ padding: '0.75rem', textAlign: 'right', fontSize: '0.85rem', color: '#9ba0af' }}>
                      [{results.bootstrap_ci.f1.ci_lower.toFixed(3)}, {results.bootstrap_ci.f1.ci_upper.toFixed(3)}]
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="insight-box" style={{ marginTop: '1.5rem', borderLeftColor: '#4E9A34' }}>
              <h4 style={{ color: '#4E9A34', marginTop: 0 }}>How to Use These Thresholds</h4>
              <p style={{ fontSize: '0.9rem', lineHeight: '1.6' }}>
                Update your MedContext configuration with these optimized values:
              </p>
              <pre style={{ background: '#1c1e26', padding: '1rem', borderRadius: '8px', overflowX: 'auto', marginTop: '0.5rem', fontSize: '0.85rem' }}>
{`# In your application code
VERACITY_THRESHOLD = ${results.optimal.veracity_threshold.toFixed(2)}
ALIGNMENT_THRESHOLD = ${results.optimal.alignment_threshold.toFixed(2)}
DECISION_LOGIC = "${results.optimal.logic}"  # Flag if veracity < threshold ${results.optimal.logic} alignment < threshold`}
              </pre>
            </div>
          </section>

          {/* Performance Metrics Comparison Chart */}
          <section className="card" style={{ marginTop: '1.5rem' }}>
            <h3>Performance Metrics Comparison</h3>
            <p className="helper">
              Comparison of all metrics with 95% confidence intervals (error bars).
            </p>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart
                data={[
                  {
                    name: 'Accuracy',
                    value: results.optimal.accuracy * 100,
                    ci_lower: results.bootstrap_ci.accuracy.ci_lower * 100,
                    ci_upper: results.bootstrap_ci.accuracy.ci_upper * 100,
                  },
                  {
                    name: 'Precision',
                    value: results.optimal.precision * 100,
                    ci_lower: results.bootstrap_ci.precision.ci_lower * 100,
                    ci_upper: results.bootstrap_ci.precision.ci_upper * 100,
                  },
                  {
                    name: 'Recall',
                    value: results.optimal.recall * 100,
                    ci_lower: results.bootstrap_ci.recall.ci_lower * 100,
                    ci_upper: results.bootstrap_ci.recall.ci_upper * 100,
                  },
                  {
                    name: 'F1 Score',
                    value: results.optimal.f1 * 100,
                    ci_lower: results.bootstrap_ci.f1.ci_lower * 100,
                    ci_upper: results.bootstrap_ci.f1.ci_upper * 100,
                  },
                ]}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <XAxis dataKey="name" stroke="#9ba0af" />
                <YAxis domain={[0, 100]} stroke="#9ba0af" label={{ value: 'Score (%)', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  contentStyle={{ background: '#1c1e26', border: '1px solid #2d3142', color: '#e9eef4', borderRadius: '8px' }}
                  formatter={(value, name, props) => [
                    `${value.toFixed(1)}% [${props.payload.ci_lower.toFixed(1)}%, ${props.payload.ci_upper.toFixed(1)}%]`,
                    name
                  ]}
                />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {[0, 1, 2, 3].map((index) => (
                    <Cell key={`cell-${index}`} fill={['#2db88a', '#5b8def', '#4E9A34', '#e5484d'][index]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </section>

          {/* Logic Comparison */}
          {results.by_logic && (
            <section className="card" style={{ marginTop: '1.5rem' }}>
              <h3>Decision Logic Comparison</h3>
              <p className="helper">
                Performance of different threshold logics (OR, AND, MIN) at their optimal configurations.
              </p>
              <div className="chart-card" style={{ marginTop: '1rem' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                  <thead>
                    <tr style={{ borderBottom: '2px solid #2d3142' }}>
                      <th style={{ padding: '0.75rem', textAlign: 'left' }}>Logic</th>
                      <th style={{ padding: '0.75rem', textAlign: 'center' }}>Veracity Threshold</th>
                      <th style={{ padding: '0.75rem', textAlign: 'center' }}>Alignment Threshold</th>
                      <th style={{ padding: '0.75rem', textAlign: 'right' }}>Accuracy</th>
                      <th style={{ padding: '0.75rem', textAlign: 'right' }}>Precision</th>
                      <th style={{ padding: '0.75rem', textAlign: 'right' }}>Recall</th>
                      <th style={{ padding: '0.75rem', textAlign: 'right' }}>F1</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(results.by_logic).map(([logic, config]) => (
                      <tr
                        key={logic}
                        style={{
                          borderBottom: '1px solid #2d3142',
                          background: logic === results.optimal.logic ? 'rgba(45, 184, 138, 0.1)' : 'transparent'
                        }}
                      >
                        <td style={{ padding: '0.75rem', fontWeight: logic === results.optimal.logic ? 600 : 400 }}>
                          {logic} {logic === results.optimal.logic && '⭐'}
                        </td>
                        <td style={{ padding: '0.75rem', textAlign: 'center' }}>{config.veracity_threshold.toFixed(2)}</td>
                        <td style={{ padding: '0.75rem', textAlign: 'center' }}>{config.alignment_threshold.toFixed(2)}</td>
                        <td style={{ padding: '0.75rem', textAlign: 'right' }}>{(config.accuracy * 100).toFixed(1)}%</td>
                        <td style={{ padding: '0.75rem', textAlign: 'right' }}>{(config.precision * 100).toFixed(1)}%</td>
                        <td style={{ padding: '0.75rem', textAlign: 'right' }}>{(config.recall * 100).toFixed(1)}%</td>
                        <td style={{ padding: '0.75rem', textAlign: 'right' }}>{config.f1.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <ResponsiveContainer width="100%" height={300} style={{ marginTop: '1.5rem' }}>
                <BarChart
                  data={Object.entries(results.by_logic).map(([logic, config]) => ({
                    logic,
                    Accuracy: config.accuracy * 100,
                    Precision: config.precision * 100,
                    Recall: config.recall * 100,
                    'F1 Score': config.f1 * 100,
                  }))}
                  margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
                >
                  <XAxis dataKey="logic" stroke="#9ba0af" />
                  <YAxis domain={[0, 100]} stroke="#9ba0af" label={{ value: 'Score (%)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip
                    contentStyle={{ background: '#1c1e26', border: '1px solid #2d3142', color: '#e9eef4', borderRadius: '8px' }}
                    formatter={(value) => `${value.toFixed(1)}%`}
                  />
                  <Legend />
                  <Bar dataKey="Accuracy" fill="#2db88a" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Precision" fill="#5b8def" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Recall" fill="#4E9A34" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="F1 Score" fill="#e5484d" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </section>
          )}

          {/* Confusion Matrix */}
          <section className="card" style={{ marginTop: '1.5rem' }}>
            <h3>Confusion Matrix</h3>
            <p className="helper">
              Breakdown of predictions: True Positives, False Positives, True Negatives, False Negatives.
            </p>
            <div className="insight-grid" style={{ marginTop: '1rem' }}>
              <div className="insight-box" style={{ borderLeftColor: '#2db88a' }}>
                <span className="insight-number" style={{ color: '#2db88a' }}>
                  {results.optimal.tp}
                </span>
                <p><strong>True Positives</strong> &mdash; correctly flagged misinformation</p>
              </div>
              <div className="insight-box" style={{ borderLeftColor: '#e5484d' }}>
                <span className="insight-number" style={{ color: '#e5484d' }}>
                  {results.optimal.fp}
                </span>
                <p><strong>False Positives</strong> &mdash; legitimate flagged as misinformation</p>
              </div>
              <div className="insight-box" style={{ borderLeftColor: '#5b8def' }}>
                <span className="insight-number" style={{ color: '#5b8def' }}>
                  {results.optimal.tn}
                </span>
                <p><strong>True Negatives</strong> &mdash; correctly identified legitimate content</p>
              </div>
              <div className="insight-box" style={{ borderLeftColor: '#f5a524' }}>
                <span className="insight-number" style={{ color: '#f5a524' }}>
                  {results.optimal.fn}
                </span>
                <p><strong>False Negatives</strong> &mdash; missed misinformation cases</p>
              </div>
            </div>

            <ResponsiveContainer width="100%" height={300} style={{ marginTop: '1.5rem' }}>
              <BarChart
                data={[
                  { name: 'True Positives', value: results.optimal.tp, fill: '#2db88a' },
                  { name: 'False Positives', value: results.optimal.fp, fill: '#e5484d' },
                  { name: 'True Negatives', value: results.optimal.tn, fill: '#5b8def' },
                  { name: 'False Negatives', value: results.optimal.fn, fill: '#f5a524' },
                ]}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <XAxis dataKey="name" stroke="#9ba0af" angle={-15} textAnchor="end" height={80} />
                <YAxis stroke="#9ba0af" label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  contentStyle={{ background: '#1c1e26', border: '1px solid #2d3142', color: '#e9eef4', borderRadius: '8px' }}
                />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {[0, 1, 2, 3].map((index, i) => (
                    <Cell key={`cell-${index}`} fill={['#2db88a', '#e5484d', '#5b8def', '#f5a524'][i]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </section>

          {results.heatmap_data && (
            <section className="card" style={{ marginTop: '1.5rem' }}>
              <h3>Threshold Sensitivity Analysis</h3>
              <p className="helper">
                Heatmap showing accuracy across all threshold combinations (darker = higher accuracy).
                The optimal point is marked in the center.
              </p>
              {/* Placeholder for heatmap visualization - would integrate with a charting library */}
              <div style={{ padding: '2rem', textAlign: 'center', background: '#1c1e26', borderRadius: '12px', marginTop: '1rem' }}>
                <p style={{ color: '#9ba0af' }}>
                  📊 Heatmap visualization available in full results (see console or download JSON)
                </p>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  )
}
