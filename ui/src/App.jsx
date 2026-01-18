import { useMemo, useState } from 'react'
import './App.css'

const defaultApiBase =
  import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const getStoredApiBase = () => {
  if (typeof window === 'undefined') {
    return defaultApiBase
  }
  const stored = window.localStorage.getItem('medcontext_api_base')
  return stored && stored.trim() ? stored : defaultApiBase
}

function App() {
  const [apiBase, setApiBase] = useState(getStoredApiBase)
  const [imageFile, setImageFile] = useState(null)
  const [imageUrl, setImageUrl] = useState('')
  const [context, setContext] = useState('')
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [fileInputKey, setFileInputKey] = useState(0)

  const hasFile = Boolean(imageFile)
  const hasUrl = imageUrl.trim().length > 0

  const statusLabel = useMemo(() => {
    if (status === 'loading') return 'Running analysis...'
    if (status === 'success') return 'Analysis complete'
    if (status === 'error') return 'Request failed'
    return 'Ready'
  }, [status])

  const handleRun = async () => {
    setError('')
    setResult(null)

    if ((hasFile && hasUrl) || (!hasFile && !hasUrl)) {
      setError('Provide either an image file or a public image URL.')
      setStatus('error')
      return
    }

    const formData = new FormData()
    if (hasFile) {
      formData.append('file', imageFile)
    }
    if (hasUrl) {
      formData.append('image_url', imageUrl.trim())
    }
    if (context.trim()) {
      formData.append('context', context.trim())
    }

    setStatus('loading')
    try {
      const response = await fetch(
        `${apiBase.replace(/\/$/, '')}/api/v1/orchestrator/run`,
        {
          method: 'POST',
          body: formData,
        },
      )
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(payload.detail || 'Request failed.')
      }
      setResult(payload)
      setStatus('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed.')
      setStatus('error')
    }
  }

  const handleApiBaseChange = (value) => {
    setApiBase(value)
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('medcontext_api_base', value)
    }
  }

  const synthesis = result?.synthesis
  const part1 = synthesis?.part_1
  const part2 = synthesis?.part_2
  const imagePreview = synthesis?.image_preview
  const contextQuote = part2?.context_quote
  const alignmentScore = useMemo(() => {
    const alignment = part2?.alignment
    if (alignment === 'aligned') {
      return {
        score: 3,
        label: 'The claim matches the image provided.',
        tone: 'high',
      }
    }
    if (alignment === 'partially_aligned') {
      return {
        score: 2,
        label: 'Some parts of the claim may relate to the image provided.',
        tone: 'medium',
      }
    }
    if (alignment === 'misaligned') {
      return {
        score: 1,
        label: 'The claim has little to no relation to the image provided.',
        tone: 'low',
      }
    }
    const verdict = typeof part2?.verdict === 'string' ? part2.verdict : ''
    const verdictLower = verdict.toLowerCase()
    if (verdictLower.includes('misinformation') || verdictLower.includes('false')) {
      return {
        score: 1,
        label: 'The claim has little to no relation to the image provided.',
        tone: 'low',
      }
    }
    if (verdictLower.includes('partial') || verdictLower.includes('mixed')) {
      return {
        score: 2,
        label: 'Some parts of the claim may relate to the image provided.',
        tone: 'medium',
      }
    }
    if (
      verdictLower.includes('true') ||
      verdictLower.includes('verified') ||
      verdictLower.includes('supported')
    ) {
      return {
        score: 3,
        label: 'The claim matches the image provided.',
        tone: 'high',
      }
    }
    return { score: 0, label: 'Alignment is unclear.', tone: 'neutral' }
  }, [part2?.alignment, part2?.verdict])
  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">MedContext</p>
          <h1>Verify medical images before you share.</h1>
          <p className="subhead">
            Upload an image or paste a public URL. MedContext checks context,
            provenance, and clinical plausibility through the API.
          </p>
        </div>
        <div className="status" aria-live="polite">
          <span className={`status-dot status-${status}`} />
          {status === 'loading' ? (
            <span className="spinner" aria-hidden="true" />
          ) : null}
          <span>{statusLabel}</span>
        </div>
      </header>

      <main className="content">
        <section className="card">
          <h2>1. Provide an image</h2>
          <div className="grid">
            <label className="field">
              <span>Image file</span>
              <input
                key={fileInputKey}
                type="file"
                accept="image/*"
                onChange={(event) =>
                  setImageFile(event.target.files?.[0] || null)
                }
              />
              <span className="helper">
                {imageFile ? imageFile.name : 'PNG, JPG, or HEIC recommended.'}
              </span>
            </label>
            <label className="field">
              <span>Public image URL</span>
              <input
                type="url"
                placeholder="https://example.com/image.jpg"
                value={imageUrl}
                onChange={(event) => setImageUrl(event.target.value)}
              />
              <span className="helper">
                Use a direct image link if possible.
              </span>
            </label>
          </div>
          <label className="field">
            <span>Optional context</span>
            <textarea
              rows="3"
              placeholder="Caption or claim about the image"
              value={context}
              onChange={(event) => setContext(event.target.value)}
            />
          </label>
          <div className="actions">
            <button
              type="button"
              onClick={handleRun}
              disabled={status === 'loading'}
            >
              Run verification
            </button>
            <button
              type="button"
              className="ghost"
              onClick={() => {
                setImageFile(null)
                setImageUrl('')
                setContext('')
                setResult(null)
                setError('')
                setStatus('idle')
                setFileInputKey((currentKey) => currentKey + 1)
              }}
            >
              Clear
            </button>
          </div>
          {error ? <p className="error">{error}</p> : null}
        </section>

        <section className="card">
          <h2>2. Results</h2>
          {result ? (
            <div className="results">
              <div className="result-block">
                <h3>Summary</h3>
                {part1 || part2 ? (
                  <div className="summary-parts">
                    <div className="summary-part">
                      <h4>Part 1: Image (factual)</h4>
                      {imagePreview ? (
                        <img
                          className="image-preview"
                          src={imagePreview}
                          alt="Reviewed upload"
                        />
                      ) : null}
                      {part1?.image_description ? (
                        <p className="summary-text">
                          {part1.image_description}
                        </p>
                      ) : (
                        <p className="summary-text">No factual description yet.</p>
                      )}
                    </div>
                    <div className="summary-part">
                      <h4>Part 2: Context analysis</h4>
                      {contextQuote ? (
                        <blockquote className="context-quote">
                          {contextQuote}
                        </blockquote>
                      ) : null}
                      {part2 ? (
                        <div className="analysis-body">
                          {alignmentScore ? (
                            <div className={`score-pill score-${alignmentScore.tone}`}>
                              <span className="score-value">
                                {alignmentScore.score}/3
                              </span>
                              <span>{alignmentScore.label}</span>
                            </div>
                          ) : null}
                          {part2.summary ? (
                            <p className="summary-text">{part2.summary}</p>
                          ) : null}
                          {part2.alignment_analysis ? (
                            <p className="summary-text">
                              {part2.alignment_analysis}
                            </p>
                          ) : null}
                          {part2.rationale ? (
                            <p className="summary-text">{part2.rationale}</p>
                          ) : null}
                          {!part2.summary &&
                          !part2.alignment_analysis &&
                          !part2.rationale ? (
                            <p className="summary-text">
                              We could not generate a detailed explanation for the
                              score. Please try again.
                            </p>
                          ) : null}
                          <div className="analysis-meta">
                            {part2.alignment ? (
                              <span>Alignment: {part2.alignment}</span>
                            ) : null}
                            {part2.verdict ? (
                              <span>Verdict: {part2.verdict}</span>
                            ) : null}
                            {part2.confidence ? (
                              <span>Confidence: {part2.confidence}</span>
                            ) : null}
                          </div>
                        </div>
                      ) : (
                        <p className="summary-text">No context analysis yet.</p>
                      )}
                    </div>
                  </div>
                ) : null}
              </div>
              <p className="helper">
                Context source: {result.context_source || 'not provided'}.
              </p>
            </div>
          ) : (
            <p className="helper">
              Run an analysis to see the contextual integrity output here.
            </p>
          )}
        </section>

      </main>
    </div>
  )
}

export default App
