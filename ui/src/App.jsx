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

  const synthesisText = result?.synthesis
    ? JSON.stringify(result.synthesis, null, 2)
    : ''
  const triageText = result?.triage
    ? JSON.stringify(result.triage, null, 2)
    : ''
  const toolResultsText = result?.tool_results
    ? JSON.stringify(result.tool_results, null, 2)
    : ''

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
        <div className="status">
          <span className={`status-dot status-${status}`} />
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
                <pre>{synthesisText || 'No synthesis yet.'}</pre>
              </div>
              <div className="result-grid">
                <div className="result-block">
                  <h3>Triage</h3>
                  <pre>{triageText || 'No triage details yet.'}</pre>
                </div>
                <div className="result-block">
                  <h3>Tool results</h3>
                  <pre>{toolResultsText || 'No tool results yet.'}</pre>
                </div>
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

        <section className="card">
          <h2>API connection</h2>
          <label className="field">
            <span>API base URL</span>
            <input
              type="text"
              value={apiBase}
              onChange={(event) => handleApiBaseChange(event.target.value)}
            />
          </label>
          <p className="helper">
            Defaults to <code>{defaultApiBase}</code>. Update this if you run the
            API elsewhere.
          </p>
        </section>
      </main>
    </div>
  )
}

export default App
