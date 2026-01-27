import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import './App.css'

const defaultApiBase =
  import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const defaultReversePollIntervalMs = 1500
const defaultReversePollTimeoutMs = 20000

const getStoredApiBase = () => {
  if (typeof window === 'undefined') {
    return defaultApiBase
  }
  const stored = window.localStorage.getItem('medcontext_api_base')
  return stored && stored.trim() ? stored : defaultApiBase
}

const getStoredNumber = (key, fallback) => {
  if (typeof window === 'undefined') {
    return fallback
  }
  const stored = window.localStorage.getItem(key)
  const parsed = stored ? Number(stored) : Number.NaN
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback
}

function App() {
  const [activeView, setActiveView] = useState('main')
  const [apiBase, setApiBase] = useState(getStoredApiBase)
  const [imageFile, setImageFile] = useState(null)
  const [imageUrl, setImageUrl] = useState('')
  const [context, setContext] = useState('')
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [fileInputKey, setFileInputKey] = useState(0)
  const [reverseImageFile, setReverseImageFile] = useState(null)
  const [reverseImageId, setReverseImageId] = useState('')
  const [reverseStatus, setReverseStatus] = useState('idle')
  const [reverseError, setReverseError] = useState('')
  const [reverseJob, setReverseJob] = useState(null)
  const [reverseResult, setReverseResult] = useState(null)
  const [reverseFileKey, setReverseFileKey] = useState(0)
  const [reversePollIntervalMs, setReversePollIntervalMs] = useState(() =>
    getStoredNumber(
      'medcontext_reverse_poll_interval_ms',
      defaultReversePollIntervalMs,
    ),
  )
  const [reversePollTimeoutMs, setReversePollTimeoutMs] = useState(() =>
    getStoredNumber(
      'medcontext_reverse_poll_timeout_ms',
      defaultReversePollTimeoutMs,
    ),
  )
  const [agentStepIndex, setAgentStepIndex] = useState(0)
  const agentStartRef = useRef(null)

  const hasFile = Boolean(imageFile)
  const hasUrl = imageUrl.trim().length > 0

  const statusLabel = useMemo(() => {
    if (status === 'loading') return 'Running analysis...'
    if (status === 'success') return 'Analysis complete'
    if (status === 'error') return 'Request failed'
    return 'Ready'
  }, [status])

  const reverseStatusLabel = useMemo(() => {
    if (reverseStatus === 'loading') return 'Searching the web...'
    if (reverseStatus === 'success') return 'Reverse search complete'
    if (reverseStatus === 'timeout') return 'Reverse search timed out'
    if (reverseStatus === 'error') return 'Reverse search failed'
    return 'Ready'
  }, [reverseStatus])

  const agentSteps = useMemo(
    () => [
      {
        key: 'triage',
        label: 'Preparing analysis',
        detail: 'We review the image and your context.',
      },
      {
        key: 'medgemma',
        label: 'MedGemma review',
        detail: 'MedGemma checks medical plausibility and context.',
      },
      {
        key: 'reverse_search',
        label: 'Checking sources',
        detail: 'Looking for where this image appears online.',
      },
      {
        key: 'forensics',
        label: 'Inspecting the image',
        detail: 'Scanning for manipulation signals and anomalies.',
      },
      {
        key: 'provenance',
        label: 'Tracing history',
        detail: 'Pulling provenance and usage clues.',
      },
      {
        key: 'synthesis',
        label: 'Finalizing',
        detail: 'Summarizing findings and generating the report.',
      },
    ],
    [],
  )

  useEffect(() => {
    if (status !== 'loading') {
      agentStartRef.current = null
      setAgentStepIndex(0)
      return
    }

    if (!agentStartRef.current) {
      agentStartRef.current = Date.now()
    }

    const stepWindowMs = 8000
    const updateStep = () => {
      const elapsed = Date.now() - (agentStartRef.current || Date.now())
      const computedIndex = Math.floor(elapsed / stepWindowMs)
      const maxIndex =
        status === 'loading' ? Math.max(0, agentSteps.length - 2) : agentSteps.length - 1
      const nextIndex = Math.min(maxIndex, computedIndex)
      setAgentStepIndex(nextIndex)
    }

    updateStep()
    const timer = window.setInterval(updateStep, 600)
    return () => window.clearInterval(timer)
  }, [agentSteps.length, status])

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

  const handleReversePollIntervalChange = (valueMs) => {
    const nextValue = Number.isFinite(valueMs) && valueMs > 0
      ? valueMs
      : defaultReversePollIntervalMs
    setReversePollIntervalMs(nextValue)
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(
        'medcontext_reverse_poll_interval_ms',
        String(nextValue),
      )
    }
  }

  const handleReversePollTimeoutChange = (valueMs) => {
    const nextValue = Number.isFinite(valueMs) && valueMs > 0
      ? valueMs
      : defaultReversePollTimeoutMs
    setReversePollTimeoutMs(nextValue)
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(
        'medcontext_reverse_poll_timeout_ms',
        String(nextValue),
      )
    }
  }

  const handleReverseSearch = async () => {
    setReverseError('')
    setReverseJob(null)
    setReverseResult(null)

    if (!reverseImageFile) {
      setReverseError('Select an image file to search.')
      setReverseStatus('error')
      return
    }

    const trimmedId = reverseImageId.trim()
    const imageId =
      trimmedId || (typeof crypto !== 'undefined' ? crypto.randomUUID() : '')

    if (!imageId) {
      setReverseError('Unable to generate an image id.')
      setReverseStatus('error')
      return
    }

    setReverseImageId(imageId)
    setReverseStatus('loading')

    const formData = new FormData()
    formData.append('file', reverseImageFile)

    try {
      const response = await fetch(
        `${apiBase.replace(/\/$/, '')}/api/v1/reverse-search/search/${imageId}`,
        {
          method: 'POST',
          body: formData,
        },
      )
      const payload = await response.json().catch(() => ({}))
      if (!response.ok) {
        throw new Error(payload.detail || 'Reverse search failed.')
      }
      setReverseJob(payload)

      const pollIntervalMs = reversePollIntervalMs
      const pollTimeoutMs = reversePollTimeoutMs
      const pollStart = Date.now()
      let resultResponse
      let resultPayload = {}

      while (Date.now() - pollStart < pollTimeoutMs) {
        resultResponse = await fetch(
          `${apiBase.replace(/\/$/, '')}/api/v1/reverse-search/results/${imageId}`,
        )
        resultPayload = await resultResponse.json().catch(() => ({}))
        if (!resultResponse.ok) {
          throw new Error(resultPayload.detail || 'Failed to fetch results.')
        }

        const terminalStatus = resultPayload?.status
        const hasResults =
          Array.isArray(resultPayload?.matches) ||
          Array.isArray(resultPayload?.results)

        if (terminalStatus === 'ready' || hasResults) {
          setReverseResult(resultPayload)
          setReverseStatus('success')
          return
        }

        if (terminalStatus === 'failed' || terminalStatus === 'error') {
          throw new Error(
            resultPayload.detail || 'Reverse search failed to complete.',
          )
        }

        await new Promise((resolve) => setTimeout(resolve, pollIntervalMs))
      }

      const timeoutError = new Error(
        resultPayload.detail || 'Reverse search timed out.',
      )
      timeoutError.name = 'TimeoutError'
      throw timeoutError
    } catch (err) {
      setReverseError(
        err instanceof Error ? err.message : 'Reverse search failed.',
      )
      setReverseStatus(err?.name === 'TimeoutError' ? 'timeout' : 'error')
    }
  }

  const synthesis = result?.synthesis
  const contextualIntegrity = synthesis?.contextual_integrity
  const part1 = synthesis?.part_1
  const part2 = synthesis?.part_2
  const imagePreview = synthesis?.image_preview
  const contextQuote = part2?.context_quote
  const reverseMatches = reverseResult?.matches || []
  const reverseProviders = reverseResult?.providers || []
  const toolResults = result?.tool_results || {}
  const forensicsData = toolResults?.forensics
  const provenanceData = toolResults?.provenance
  const orchestratorReverseSearch = toolResults?.reverse_search
  const toolActivity = useMemo(
    () => ({
      reverse_search: Boolean(orchestratorReverseSearch),
      forensics: Boolean(forensicsData),
      provenance: Boolean(provenanceData),
    }),
    [forensicsData, orchestratorReverseSearch, provenanceData],
  )
  const agentStepStates = useMemo(() => {
    const hasAnyToolActivity = Object.values(toolActivity).some(Boolean)
    return agentSteps.map((step, index) => {
      if (status === 'success') {
        if (step.key in toolActivity) {
          return toolActivity[step.key] ? 'done' : 'skipped'
        }
        return 'done'
      }
      if (status === 'error') {
        if (step.key in toolActivity) {
          return toolActivity[step.key] ? 'done' : 'skipped'
        }
        return hasAnyToolActivity ? 'skipped' : 'idle'
      }
      if (status === 'loading') {
        if (step.key === 'medgemma') {
          return hasAnyToolActivity ? 'done' : 'active'
        }
        if (step.key in toolActivity && toolActivity[step.key]) {
          return 'done'
        }
        if (index < agentStepIndex) return 'done'
        if (index === agentStepIndex) return 'active'
        return 'pending'
      }
      return 'idle'
    })
  }, [agentStepIndex, agentSteps, status, toolActivity])
  const integrityVisualization = contextualIntegrity?.visualization || null
  const integrityScore =
    typeof integrityVisualization?.overall_confidence === 'number'
      ? integrityVisualization.overall_confidence
      : typeof contextualIntegrity?.score === 'number'
        ? contextualIntegrity.score
        : null
  const integritySignals =
    integrityVisualization || contextualIntegrity?.signals || null
  const integrityScorePercent =
    integrityScore === null ? null : Math.round(integrityScore * 100)
  const integrityScoreTone =
    integrityScorePercent === null
      ? 'neutral'
      : integrityScorePercent >= 70
        ? 'high'
        : integrityScorePercent >= 40
          ? 'medium'
          : 'low'
  const integrityScoreData = useMemo(() => {
    if (integrityScorePercent === null) return []
    return [
      { name: 'score', value: integrityScorePercent },
      { name: 'remaining', value: 100 - integrityScorePercent },
    ]
  }, [integrityScorePercent])
  const integritySignalData = useMemo(() => {
    if (!integritySignals) return []
    const palette = {
      alignment: '#4f7cff',
      plausibility: '#2db88a',
      genealogy_consistency: '#f5a524',
      source_reputation: '#6d7d93',
      alignment_confidence: '#4f7cff',
      plausibility_confidence: '#2db88a',
      genealogy_confidence: '#f5a524',
      source_confidence: '#6d7d93',
    }
    return Object.entries(integritySignals)
      .filter(([key, value]) => key !== 'overall_confidence' && typeof value === 'number')
      .map(([key, value]) => ({
        key,
        label: key.replace(/_/g, ' ').replace('confidence', '').trim(),
        value: Math.round(value * 100),
        fill: palette[key] || '#5b8def',
      }))
  }, [integritySignals])
  const alignmentScore = useMemo(() => {
    const alignment =
      typeof part2?.alignment === 'string' ? part2.alignment : ''
    const alignmentKey = alignment.toLowerCase().replace(/[\s-]+/g, '_')
    if (alignmentKey === 'aligned') {
      return {
        score: 3,
        label: 'The claim matches the image provided.',
        tone: 'high',
      }
    }
    if (alignmentKey === 'partially_aligned') {
      return {
        score: 2,
        label: 'Some parts of the claim may relate to the image provided.',
        tone: 'medium',
      }
    }
    if (alignmentKey === 'misaligned') {
      return {
        score: 1,
        label: 'The claim has little to no relation to the image provided.',
        tone: 'low',
      }
    }
    const verdict = typeof part2?.verdict === 'string' ? part2.verdict : ''
    const verdictLower = verdict.toLowerCase()
    // Check partial/mixed first to avoid "partially false" matching "false"
    if (verdictLower.includes('partial') || verdictLower.includes('mixed')) {
      return {
        score: 2,
        label: 'Some parts of the claim may relate to the image provided.',
        tone: 'medium',
      }
    }
    if (verdictLower.includes('misinformation') || verdictLower.includes('false')) {
      return {
        score: 1,
        label: 'The claim has little to no relation to the image provided.',
        tone: 'low',
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
  const evidenceItems = useMemo(() => {
    const items = []
    if (part2?.alignment) {
      items.push({
        label: 'Alignment signal',
        value: part2.alignment,
        detail: alignmentScore.label,
        tone: alignmentScore.tone,
      })
    }
    if (integrityScorePercent !== null) {
      items.push({
        label: 'Integrity score',
        value: `${integrityScorePercent}%`,
        detail: 'Composite score across evidence signals.',
        tone: integrityScoreTone,
      })
    }
    if (orchestratorReverseSearch) {
      const matchCount = orchestratorReverseSearch.matches?.length || 0
      items.push({
        label: 'Reverse search',
        value: `${matchCount} matches`,
        detail: matchCount ? 'Sources found online.' : 'No sources found.',
        tone: matchCount ? 'high' : 'neutral',
      })
    }
    if (provenanceData) {
      const blockCount = provenanceData.blocks?.length || 0
      items.push({
        label: 'Provenance chain',
        value: `${blockCount} blocks`,
        detail: blockCount ? 'Immutable chain constructed.' : 'No chain data.',
        tone: blockCount ? 'high' : 'neutral',
      })
    }
    if (forensicsData) {
      const statusLabel =
        typeof forensicsData?.status === 'string' ? forensicsData.status : 'unknown'
      items.push({
        label: 'Forensics status',
        value: statusLabel,
        detail: forensicsData?.detail || 'No forensics detail returned.',
        tone: statusLabel === 'completed' ? 'high' : 'neutral',
      })
    }
    return items
  }, [
    alignmentScore.label,
    alignmentScore.tone,
    forensicsData,
    integrityScorePercent,
    integrityScoreTone,
    orchestratorReverseSearch,
    part2?.alignment,
    provenanceData,
  ])
  return (
    <div className="page">
      <header className="hero">
        <div className="hero-brand">
          <img
            className="hero-logo"
            src="/medContext-logo.png"
            alt="MedContext logo"
          />
          <div>
            <p className="eyebrow">MedContext</p>
            <h1>Medical images don&apos;t need to be fake to cause harm.</h1>
            <p className="subhead">
              Check your image context with MedContext.
            </p>
          </div>
        </div>
        <div className="hero-actions">
          <div className="status" aria-live="polite">
            <span className={`status-dot status-${status}`} />
            {status === 'loading' ? (
              <span className="spinner" aria-hidden="true" />
            ) : null}
            <span>{statusLabel}</span>
          </div>
          <button
            type="button"
            className="ghost"
            onClick={() =>
              setActiveView((current) =>
                current === 'settings' ? 'main' : 'settings',
              )
            }
          >
            {activeView === 'settings' ? 'Back to app' : 'Settings'}
          </button>
        </div>
      </header>

      <main className="content">
        {activeView === 'settings' ? (
          <section className="card settings-card">
            <div className="settings-header">
              <div>
                <h2>Settings</h2>
                <p className="helper">
                  Configure API endpoints and reverse search polling.
                </p>
              </div>
            </div>
            <div className="settings-section">
              <h3>API</h3>
              <div className="grid">
                <label className="field">
                  <span>API base URL</span>
                  <input
                    type="url"
                    placeholder={defaultApiBase}
                    value={apiBase}
                    onChange={(event) =>
                      handleApiBaseChange(event.target.value)
                    }
                  />
                  <span className="helper">
                    Stored locally in your browser.
                  </span>
                </label>
              </div>
            </div>
            <div className="settings-section">
              <h3>Reverse search polling</h3>
              <div className="grid">
                <label className="field">
                  <span>Polling interval (ms)</span>
                  <input
                    type="number"
                    min="500"
                    step="100"
                    value={reversePollIntervalMs}
                    onChange={(event) => {
                      const nextValue = Number(event.target.value)
                      handleReversePollIntervalChange(
                        Number.isFinite(nextValue) && nextValue > 0
                          ? nextValue
                          : reversePollIntervalMs,
                      )
                    }}
                  />
                  <span className="helper">
                    How often the UI checks for results.
                  </span>
                </label>
                <label className="field">
                  <span>Timeout (ms)</span>
                  <input
                    type="number"
                    min="1000"
                    step="500"
                    value={reversePollTimeoutMs}
                    onChange={(event) => {
                      const nextValue = Number(event.target.value)
                      handleReversePollTimeoutChange(
                        Number.isFinite(nextValue) && nextValue > 0
                          ? nextValue
                          : reversePollTimeoutMs,
                      )
                    }}
                  />
                  <span className="helper">
                    Max time to wait before timing out.
                  </span>
                </label>
              </div>
            </div>
          </section>
        ) : (
          <>
            <div className="top-grid">
              <section className="card activity-card">
                <div className="reverse-header">
                  <div>
                    <h2>Progress</h2>
                    <p className="helper">
                      Live status updates while we work on your request.
                    </p>
                  </div>
                </div>
                <div className="activity-grid">
                  {agentSteps.map((step, index) => {
                    const state = agentStepStates[index]
                    return (
                      <div
                        className={`activity-step activity-${state}`}
                        key={step.key}
                      >
                        <div className="activity-header">
                          <span>{step.label}</span>
                          <span className={`activity-pill activity-${state}`}>
                            {state}
                          </span>
                        </div>
                        <p className="helper">{step.detail}</p>
                      </div>
                    )
                  })}
                </div>
              </section>
              <section className="card">
                <h2>Provide an image</h2>
                <div className="inline-status" aria-live="polite">
                  <span className={`status-dot status-${status}`} />
                  {status === 'loading' ? (
                    <span className="spinner" aria-hidden="true" />
                  ) : null}
                  <span>{statusLabel}</span>
                </div>
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
                      {imageFile
                        ? imageFile.name
                        : 'PNG, JPG, or HEIC recommended.'}
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
            </div>

            <section className="card">
              <div className="reverse-header">
                <div>
                  <h2>Reverse image search</h2>
                  <p className="helper">
                    Upload an image to find matching sources via SerpAPI.
                  </p>
                </div>
                <div className="status" aria-live="polite">
                  <span className={`status-dot status-${reverseStatus}`} />
                  {reverseStatus === 'loading' ? (
                    <span className="spinner" aria-hidden="true" />
                  ) : null}
                  <span>{reverseStatusLabel}</span>
                </div>
              </div>
              <div className="grid">
                <label className="field">
                  <span>Image file</span>
                  <input
                    key={reverseFileKey}
                    type="file"
                    accept="image/*"
                    onChange={(event) =>
                      setReverseImageFile(event.target.files?.[0] || null)
                    }
                  />
                  <span className="helper">
                    {reverseImageFile
                      ? reverseImageFile.name
                      : 'Provide the image to search.'}
                  </span>
                </label>
                <label className="field">
                  <span>Image ID (optional)</span>
                  <input
                    type="text"
                    placeholder="Leave blank to auto-generate"
                    value={reverseImageId}
                    onChange={(event) => setReverseImageId(event.target.value)}
                  />
                  <span className="helper">
                    Used to retrieve results from the API cache.
                  </span>
                </label>
              </div>
              <div className="actions">
                <button
                  type="button"
                  onClick={handleReverseSearch}
                  disabled={reverseStatus === 'loading'}
                >
                  Run reverse search
                </button>
                <button
                  type="button"
                  className="ghost"
                  onClick={() => {
                    setReverseImageFile(null)
                    setReverseImageId('')
                    setReverseJob(null)
                    setReverseResult(null)
                    setReverseError('')
                    setReverseStatus('idle')
                    setReverseFileKey((currentKey) => currentKey + 1)
                  }}
                >
                  Clear
                </button>
              </div>
              {reverseError ? <p className="error">{reverseError}</p> : null}
              {reverseResult ? (
                <div className="results">
                  <div className="reverse-meta">
                    <span>Image ID: {reverseResult.image_id}</span>
                    {reverseResult.query_hash ? (
                      <span>Query hash: {reverseResult.query_hash}</span>
                    ) : null}
                    {reverseProviders.length ? (
                      <span>Providers: {reverseProviders.join(', ')}</span>
                    ) : null}
                  </div>
                  {reverseMatches.length ? (
                    <div className="match-grid">
                      {reverseMatches.map((match) => (
                        <article className="match-card" key={match.url}>
                          <div className="match-header">
                            <span className="pill">{match.source}</span>
                            <span className="pill pill-muted">
                              {Math.round(match.confidence * 100)}% confidence
                            </span>
                          </div>
                          <h3>{match.title || 'Untitled match'}</h3>
                          {match.snippet ? (
                            <p className="summary-text">{match.snippet}</p>
                          ) : null}
                          <a href={match.url} target="_blank" rel="noreferrer">
                            {match.url}
                          </a>
                          {match.metadata ? (
                            <p className="helper">
                              Metadata: {Object.keys(match.metadata).length} fields
                            </p>
                          ) : null}
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="helper">
                      No matches returned. Try another image or check SerpAPI status.
                    </p>
                  )}
                </div>
              ) : reverseJob ? (
                <p className="helper">
                  Reverse search queued. Image ID: {reverseJob.image_id}
                </p>
              ) : null}
            </section>

            <section className="card">
              <h2>Contextual integrity results</h2>
              {result ? (
                <div className="results">
                  <div className="result-block">
                    <h3>Summary</h3>
                    {part1 || part2 ? (
                      <div className="summary-parts">
                        <div className="summary-part">
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
                  {contextualIntegrity ? (
                    <div className="result-block">
                      <h3>Evidence signals</h3>
                      {contextualIntegrity.usage_assessment ? (
                        <p className="helper">
                          Usage assessment: {contextualIntegrity.usage_assessment}
                        </p>
                      ) : null}
                      <div className="viz-grid">
                        <div className={`viz-card viz-score viz-${integrityScoreTone}`}>
                          <div className="viz-metric">
                            <span>Contextual integrity score</span>
                            <strong>
                              {integrityScorePercent === null
                                ? '—'
                                : `${integrityScorePercent}%`}
                            </strong>
                          </div>
                          {integrityScoreData.length ? (
                            <div className="viz-chart">
                              <ResponsiveContainer width="100%" height={180}>
                                <PieChart>
                                  <Pie
                                    data={integrityScoreData}
                                    dataKey="value"
                                    innerRadius={55}
                                    outerRadius={75}
                                    startAngle={90}
                                    endAngle={-270}
                                    paddingAngle={2}
                                    stroke="none"
                                  >
                                    {integrityScoreData.map((entry, index) => (
                                      <Cell
                                        // eslint-disable-next-line react/no-array-index-key
                                        key={`score-${index}`}
                                        fill={
                                          entry.name === 'score'
                                            ? integrityScoreTone === 'high'
                                              ? '#2db88a'
                                              : integrityScoreTone === 'medium'
                                                ? '#f5a524'
                                                : '#e5484d'
                                            : '#e9eef4'
                                        }
                                      />
                                    ))}
                                  </Pie>
                                  <Tooltip formatter={(value) => `${value}%`} />
                                </PieChart>
                              </ResponsiveContainer>
                            </div>
                          ) : (
                            <p className="helper">No integrity score available.</p>
                          )}
                        </div>
                        <div className="viz-card">
                          <div className="viz-metric">
                            <span>Signal contributions</span>
                            <strong>0–100</strong>
                          </div>
                          {integritySignalData.length ? (
                            <div className="viz-chart">
                              <ResponsiveContainer width="100%" height={220}>
                                <BarChart
                                  data={integritySignalData}
                                  layout="vertical"
                                  margin={{ left: 20, right: 12 }}
                                >
                                  <XAxis type="number" domain={[0, 100]} hide />
                                  <YAxis
                                    type="category"
                                    dataKey="label"
                                    width={120}
                                  />
                                  <Tooltip formatter={(value) => `${value}%`} />
                                  <Bar dataKey="value" isAnimationActive={false}>
                                    {integritySignalData.map((entry) => (
                                      <Cell key={entry.key} fill={entry.fill} />
                                    ))}
                                  </Bar>
                                </BarChart>
                              </ResponsiveContainer>
                            </div>
                          ) : (
                            <p className="helper">No signal data available.</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ) : null}
                  {evidenceItems.length ? (
                    <div className="result-block">
                      <h3>Explainability highlights</h3>
                      <div className="evidence-grid">
                        {evidenceItems.map((item) => (
                          <div
                            key={`${item.label}-${item.value}`}
                            className={`evidence-card evidence-${item.tone}`}
                          >
                            <span className="evidence-label">{item.label}</span>
                            <strong className="evidence-value">{item.value}</strong>
                            <p className="helper">{item.detail}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : null}
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

            {/* Forensics Tool Results */}
            {forensicsData ? (
              <section className="card">
                <h2>🔍 Forensics Analysis</h2>
                <p className="helper">
                  Forensics signals and metadata checks (legacy integrity checks removed).
                </p>
                {forensicsData.results ? (
                  <div className="results">
                    {Object.entries(forensicsData.results).map(([layerName, layerData]) => (
                      <div key={layerName} className="result-block">
                        <h3>
                          {layerName === 'layer_1' ? '📊 Layer 1: Pixel Forensics (ELA)' :
                            layerName === 'layer_2' ? '🧠 Layer 2: Semantic Analysis' :
                              '📝 Layer 3: Metadata & EXIF'}
                        </h3>
                        <div className="forensics-verdict">
                          <span className={`pill ${layerData.verdict === 'AUTHENTIC' ? 'pill-success' : layerData.verdict === 'MANIPULATED' ? 'pill-error' : 'pill-warning'}`}>
                            {layerData.verdict}
                          </span>
                          <span className="pill pill-muted">
                            {Math.round(layerData.confidence * 100)}% confidence
                          </span>
                        </div>
                        {layerData.details ? (
                          <div className="forensics-details">
                            {layerData.details.method ? (
                              <p><strong>Method:</strong> {layerData.details.method}</p>
                            ) : null}
                            {layerData.details.ela_mean !== undefined ? (
                              <div className="forensics-stats">
                                <p><strong>ELA Mean:</strong> {layerData.details.ela_mean}</p>
                                <p><strong>ELA Std Dev:</strong> {layerData.details.ela_std}</p>
                                <p><strong>ELA Max:</strong> {layerData.details.ela_max}</p>
                                {layerData.details.image_size ? (
                                  <p><strong>Image Size:</strong> {layerData.details.image_size[0]} x {layerData.details.image_size[1]}</p>
                                ) : null}
                              </div>
                            ) : null}
                            {layerData.details.has_exif !== undefined ? (
                              <div>
                                <p><strong>EXIF Data:</strong> {layerData.details.has_exif ? 'Present' : 'Missing'}</p>
                                {layerData.details.exif_fields_count ? (
                                  <p><strong>EXIF Fields:</strong> {layerData.details.exif_fields_count}</p>
                                ) : null}
                                {layerData.details.suspicious_patterns?.length > 0 ? (
                                  <div className="suspicious-patterns">
                                    <p><strong>⚠️ Suspicious Patterns:</strong></p>
                                    <ul>
                                      {layerData.details.suspicious_patterns.map((pattern, idx) => (
                                        <li key={idx} className="error">{pattern}</li>
                                      ))}
                                    </ul>
                                  </div>
                                ) : null}
                                {layerData.details.software_tags?.length > 0 ? (
                                  <p><strong>Software:</strong> {layerData.details.software_tags.join(', ')}</p>
                                ) : null}
                              </div>
                            ) : null}
                            {layerData.details.note ? (
                              <p className="helper">{layerData.details.note}</p>
                            ) : null}
                            {layerData.details.error ? (
                              <p className="error">Error: {layerData.details.error}</p>
                            ) : null}
                          </div>
                        ) : null}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="helper">
                    Forensics layers are currently unavailable.
                  </p>
                )}
              </section>
            ) : null}

            {/* Provenance Tool Results */}
            {provenanceData ? (
              <section className="card">
                <h2>🔗 Provenance Chain</h2>
                <p className="helper">
                  Blockchain-style immutable audit trail for image history
                </p>
                <div className="results">
                  <div className="provenance-meta">
                    <p><strong>Chain ID:</strong> <code>{provenanceData.chain_id}</code></p>
                    <p><strong>Status:</strong> <span className="pill pill-success">{provenanceData.status}</span></p>
                    <p><strong>Blocks:</strong> {provenanceData.blocks?.length || 0}</p>
                  </div>
                  {provenanceData.blocks?.length > 0 ? (
                    <div className="provenance-blocks">
                      {provenanceData.blocks.map((block, idx) => (
                        <div key={idx} className="provenance-block">
                          <div className="block-header">
                            <strong>Block #{block.block_number}</strong>
                            <span className="pill pill-muted">{block.observation_type}</span>
                          </div>
                          <div className="block-hash">
                            <p><strong>Hash:</strong> <code>{block.block_hash?.substring(0, 16)}...</code></p>
                            {block.previous_hash ? (
                              <p><strong>Previous:</strong> <code>{block.previous_hash.substring(0, 16)}...</code></p>
                            ) : (
                              <p><strong>Previous:</strong> <em>Genesis block</em></p>
                            )}
                          </div>
                          {block.observation_data ? (
                            <details>
                              <summary>View observation data</summary>
                              <pre className="code-block">{JSON.stringify(block.observation_data, null, 2)}</pre>
                            </details>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="helper">No provenance blocks available</p>
                  )}
                </div>
              </section>
            ) : null}

            {/* Orchestrator Reverse Search Results */}
            {orchestratorReverseSearch ? (
              <section className="card">
                <h2>🔎 Reverse Search (from Agent)</h2>
                <p className="helper">
                  Agent-invoked reverse image search results
                </p>
                <div className="results">
                  <div className="reverse-meta">
                    <span>Image ID: {orchestratorReverseSearch.image_id}</span>
                    {orchestratorReverseSearch.query_hash ? (
                      <span>Query Hash: {orchestratorReverseSearch.query_hash}</span>
                    ) : null}
                  </div>
                  {orchestratorReverseSearch.matches?.length > 0 ? (
                    <div className="match-grid">
                      {orchestratorReverseSearch.matches.map((match, idx) => (
                        <article className="match-card" key={idx}>
                          <div className="match-header">
                            <span className="pill">{match.source || 'Unknown'}</span>
                            {match.confidence ? (
                              <span className="pill pill-muted">
                                {Math.round(match.confidence * 100)}% confidence
                              </span>
                            ) : null}
                          </div>
                          <h3>{match.title || 'Untitled match'}</h3>
                          {match.snippet ? (
                            <p className="summary-text">{match.snippet}</p>
                          ) : null}
                          {match.url ? (
                            <a href={match.url} target="_blank" rel="noreferrer">
                              {match.url}
                            </a>
                          ) : null}
                        </article>
                      ))}
                    </div>
                  ) : (
                    <p className="helper">No matches found via agent-invoked reverse search</p>
                  )}
                </div>
              </section>
            ) : null}
          </>
        )}
      </main>
    </div>
  )
}

export default App
