import { useEffect, useMemo, useState } from 'react'
import './App.css'
import ValidationStory from './ValidationStory'

function renderTriIcon(status, cx, cy) {
  if (status === 'pass') {
    return (
      <path
        d={`M${cx - 12},${cy + 1} L${cx - 3},${cy + 10} L${cx + 14},${cy - 9}`}
        stroke="#fff"
        strokeWidth="5"
        fill="none"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    )
  }
  if (status === 'fail') {
    return (
      <g>
        <line x1={cx - 10} y1={cy - 10} x2={cx + 10} y2={cy + 10} stroke="#fff" strokeWidth="5" strokeLinecap="round" />
        <line x1={cx + 10} y1={cy - 10} x2={cx - 10} y2={cy + 10} stroke="#fff" strokeWidth="5" strokeLinecap="round" />
      </g>
    )
  }
  if (status === 'partial') {
    return (
      <g>
        <line x1={cx - 10} y1={cy} x2={cx + 10} y2={cy} stroke="#fff" strokeWidth="5" strokeLinecap="round" />
      </g>
    )
  }
  if (status === 'addon') {
    return (
      <text x={cx} y={cy + 7} textAnchor="middle" fill="#fff" fontSize="22" fontWeight="700">+</text>
    )
  }
  return (
    <text x={cx} y={cy + 7} textAnchor="middle" fill="#fff" fontSize="24" fontWeight="700">?</text>
  )
}

const defaultApiBase =
  import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const getStoredApiBase = () => {
  if (typeof window === 'undefined') {
    return defaultApiBase
  }
  const stored = window.localStorage.getItem('medcontext_api_base')
  return stored && stored.trim() ? stored : defaultApiBase
}

const getStoredAccessCode = () => {
  if (typeof window === 'undefined') {
    return ''
  }
  return window.localStorage.getItem('medcontext_access_code') || ''
}


function App() {
  const [activeView, setActiveView] = useState('main')
  const [apiBase, setApiBase] = useState(getStoredApiBase)
  const [accessCode, setAccessCode] = useState(getStoredAccessCode)
  const [imageFile, setImageFile] = useState(null)
  const [imageUrl, setImageUrl] = useState('')
  const [context, setContext] = useState('')
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [fileInputKey, setFileInputKey] = useState(0)
  const [modules, setModules] = useState(null)

  const hasFile = Boolean(imageFile)
  const hasUrl = imageUrl.trim().length > 0

  // Fetch module status on mount and when API base changes
  useEffect(() => {
    const fetchModules = async () => {
      try {
        const headers = {}
        if (accessCode.trim()) {
          headers['X-Demo-Access-Code'] = accessCode.trim()
        }
        const res = await fetch(
          `${apiBase.replace(/\/$/, '')}/api/v1/modules`,
          { headers },
        )
        if (res.ok) {
          const data = await res.json()
          const moduleMap = {}
          for (const m of data.modules || []) {
            moduleMap[m.name] = m
          }
          setModules(moduleMap)
        }
      } catch {
        // Module endpoint unavailable — assume all enabled for backwards compat
      }
    }
    fetchModules()
  }, [apiBase, accessCode])

  const isAddonEnabled = (name) => {
    if (!modules) return true // backwards compat: if endpoint unavailable, show all
    return modules[name]?.enabled ?? false
  }


  const statusLabel = useMemo(() => {
    if (status === 'loading') return 'Running analysis...'
    if (status === 'success') return 'Analysis complete'
    if (status === 'error') return 'Request failed'
    return 'Ready'
  }, [status])

  const agentSteps = [
    {
      key: 'image_integrity',
      label: 'Image Integrity',
      detail: 'Pixel forensics, metadata, and manipulation detection.',
      toolKey: 'forensics',
    },
    {
      key: 'contextual_authenticity',
      label: 'Contextual Authenticity',
      detail: 'MedGemma evaluates claim veracity and context alignment.',
      toolKey: null,
    },
    {
      key: 'source_verification',
      label: 'Source Verification',
      detail: 'Reverse image search to find where this image appears online.',
      toolKey: 'reverse_search',
    },
    {
      key: 'provenance',
      label: 'Provenance',
      detail: 'Immutable audit trail and usage history for the image.',
      toolKey: 'provenance',
    },
  ]

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
      const headers = {}
      if (accessCode.trim()) {
        headers['X-Demo-Access-Code'] = accessCode.trim()
      }
      const response = await fetch(
        `${apiBase.replace(/\/$/, '')}/api/v1/orchestrator/run`,
        {
          method: 'POST',
          headers,
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

  const handleAccessCodeChange = (value) => {
    setAccessCode(value)
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('medcontext_access_code', value)
    }
  }

  const synthesis = result?.synthesis
  const contextualIntegrity = synthesis?.contextual_integrity
  const part1 = synthesis?.part_1
  const part2 = synthesis?.part_2
  const imagePreview = synthesis?.image_preview
  const userContextQuote =
    typeof context === 'string' && context.trim() ? context.trim() : null
  const contextQuote = userContextQuote ?? part2?.context_quote
  const isUserProvidedContext = Boolean(userContextQuote)
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
    return agentSteps.map((step) => {
      if (status === 'idle') return 'idle'
      if (status === 'loading') return 'pending'
      // success or error: reflect what the triage agent actually selected
      if (step.toolKey === null) {
        // Contextual Authenticity always runs
        return status === 'success' ? 'done' : 'idle'
      }
      return toolActivity[step.toolKey] ? 'done' : 'skipped'
    })
  }, [agentSteps, status, toolActivity])
  const integrityVisualization = contextualIntegrity?.visualization || null
  const integrityScore =
    typeof integrityVisualization?.overall_confidence === 'number'
      ? integrityVisualization.overall_confidence
      : typeof contextualIntegrity?.score === 'number'
        ? contextualIntegrity.score
        : null
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
  const claimVeracity = useMemo(() => {
    const veracity =
      part2?.claim_veracity || contextualIntegrity?.claim_veracity || null
    if (!veracity || typeof veracity !== 'object') {
      return null
    }
    const accuracy = typeof veracity.factual_accuracy === 'string'
      ? veracity.factual_accuracy.toLowerCase()
      : null
    const toneMap = {
      accurate: 'high',
      partially_accurate: 'medium',
      inaccurate: 'low',
      unverifiable: 'neutral',
    }
    const labelMap = {
      accurate: 'Claim is factually accurate',
      partially_accurate: 'Claim is partially accurate',
      inaccurate: 'Claim is factually inaccurate',
      unverifiable: 'Claim veracity could not be determined',
    }
    return {
      accuracy,
      tone: toneMap[accuracy] || 'neutral',
      label: labelMap[accuracy] || 'Claim veracity unknown',
      evidenceBasis: veracity.evidence_basis || null,
      publicHealthContext: veracity.public_health_context || null,
    }
  }, [part2?.claim_veracity, contextualIntegrity?.claim_veracity])
  const alignmentScore = useMemo(() => {
    const alignment =
      typeof part2?.alignment === 'string' ? part2.alignment : ''
    const alignmentKey = alignment.toLowerCase().replace(/[\s-]+/g, '_')
    if (alignmentKey === 'aligned') {
      return {
        score: 3,
        label: 'The image-claim pair is contextually appropriate.',
        tone: 'high',
      }
    }
    if (alignmentKey === 'partially_aligned') {
      return {
        score: 2,
        label: 'The image is consistent with the claim, but specific causation is unverifiable.',
        tone: 'medium',
      }
    }
    if (alignmentKey === 'misaligned') {
      return {
        score: 1,
        label: 'The claim contradicts or is unrelated to the image.',
        tone: 'low',
      }
    }
    const verdict = typeof part2?.verdict === 'string' ? part2.verdict : ''
    const verdictLower = verdict.toLowerCase()
    if (verdictLower.includes('partial') || verdictLower.includes('mixed')) {
      return {
        score: 2,
        label: 'The image is consistent with the claim, but specific causation is unverifiable.',
        tone: 'medium',
      }
    }
    if (verdictLower.includes('misinformation') || verdictLower.includes('false')) {
      return {
        score: 1,
        label: 'The claim contradicts or is unrelated to the image.',
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
        label: 'The image-claim pair is contextually appropriate.',
        tone: 'high',
      }
    }
    return { score: 0, label: 'Alignment undetermined.', tone: 'neutral' }
  }, [part2?.alignment, part2?.verdict])
  const evidenceItems = useMemo(() => {
    const items = []
    if (part2?.alignment) {
      items.push({
        label: 'Image-claim alignment',
        value: part2.alignment,
        detail: alignmentScore.label,
        tone: alignmentScore.tone,
      })
    }
    if (claimVeracity?.accuracy) {
      items.push({
        label: 'Claim veracity',
        value: claimVeracity.accuracy.replace('_', ' '),
        detail: claimVeracity.evidenceBasis || claimVeracity.label,
        tone: claimVeracity.tone,
      })
    }
    if (integrityScorePercent !== null) {
      items.push({
        label: 'Authenticity score',
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
      const isAnchored = Boolean(provenanceData.blockchain_tx_hash)
      items.push({
        label: 'Provenance chain',
        value: `${blockCount} blocks`,
        detail: isAnchored
          ? 'Immutable chain anchored on Polygon blockchain.'
          : blockCount
            ? 'Immutable chain constructed.'
            : 'No chain data.',
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
    claimVeracity,
    forensicsData,
    integrityScorePercent,
    integrityScoreTone,
    orchestratorReverseSearch,
    part2?.alignment,
    provenanceData,
  ])
  const assessmentQuadrant = useMemo(() => {
    if (!part2?.alignment && !claimVeracity) return null
    const alignmentKey = (part2?.alignment || '').toLowerCase().replace(/[\s-]+/g, '_')
    const isAligned = alignmentKey === 'aligned' || alignmentKey === 'partially_aligned'
    const accuracy = claimVeracity?.accuracy || ''
    const isAccurate = accuracy === 'accurate' || accuracy === 'partially_accurate'
    const hasVeracity = Boolean(accuracy)
    if (isAligned && isAccurate) {
      return {
        quadrant: 'aligned-accurate',
        title: 'Verified context',
        description: 'The claim is factually sound and the image supports it.',
        tone: 'high',
      }
    }
    if (isAligned && !isAccurate) {
      return {
        quadrant: 'aligned-inaccurate',
        title: hasVeracity ? 'Image supports false claim' : 'Alignment only',
        description: hasVeracity
          ? 'The image matches the claim, but the claim itself is factually wrong. This is potentially dangerous misinformation.'
          : 'Image aligns with the claim. Claim veracity was not assessed.',
        tone: hasVeracity ? 'danger' : 'medium',
      }
    }
    if (!isAligned && isAccurate) {
      return {
        quadrant: 'misaligned-accurate',
        title: 'True claim, wrong image',
        description: 'The claim is factually accurate, but this image does not support or illustrate it.',
        tone: 'medium',
      }
    }
    if (!isAligned && !isAccurate && hasVeracity) {
      return {
        quadrant: 'misaligned-inaccurate',
        title: 'False claim, wrong image',
        description: 'The claim is factually wrong and the image does not support it.',
        tone: 'low',
      }
    }
    return {
      quadrant: 'unknown',
      title: 'Assessment incomplete',
      description: 'Alignment or veracity could not be fully determined.',
      tone: 'neutral',
    }
  }, [claimVeracity, part2?.alignment])
  const triangleSignals = useMemo(() => {
    const getForensicsStatus = () => {
      if (!isAddonEnabled('forensics')) return 'addon'
      if (!forensicsData) return 'unchecked'
      if (forensicsData.results) {
        const layers = Object.values(forensicsData.results)
        if (layers.some(l => l.verdict === 'MANIPULATED')) return 'fail'
        if (layers.some(l => l.verdict === 'AUTHENTIC')) return 'pass'
      }
      return 'unchecked'
    }

    const getVeracityStatus = () => {
      if (!claimVeracity) return 'unchecked'
      if (claimVeracity.tone === 'high') return 'pass'
      if (claimVeracity.tone === 'medium') return 'partial'
      if (claimVeracity.tone === 'low') return 'fail'
      return 'unchecked'
    }

    const getAlignmentStatus = () => {
      if (!alignmentScore || alignmentScore.score === 0) return 'unchecked'
      if (alignmentScore.tone === 'high') return 'pass'
      if (alignmentScore.tone === 'medium') return 'partial'
      if (alignmentScore.tone === 'low') return 'fail'
      return 'unchecked'
    }

    const integrity = getForensicsStatus()
    const veracity = getVeracityStatus()
    const alignment = getAlignmentStatus()

    const checked = [integrity, veracity, alignment].filter(s => s !== 'unchecked' && s !== 'addon')
    let overall = 'unchecked'
    if (checked.length > 0) {
      if (checked.every(s => s === 'pass')) overall = 'pass'
      else if (checked.some(s => s === 'fail')) overall = 'fail'
      else overall = 'partial'
    }

    return { integrity, veracity, alignment, overall }
  }, [forensicsData, claimVeracity, alignmentScore])

  // 2x2x2 matrix: which of the 8 cells is active
  const cubeMatrix = useMemo(() => {
    if (!triangleSignals) return null
    const { integrity, veracity, alignment } = triangleSignals
    // Only show matrix if at least veracity and alignment are checked
    if (veracity === 'unchecked' && alignment === 'unchecked') return null

    const intFail = integrity === 'fail'
    const verFail = veracity === 'fail'
    const aliFail = alignment === 'fail'

    // Determine active cell key: integrity-veracity-alignment
    // Each can be P(ass) or F(ail)
    const iKey = intFail ? 'F' : 'P'
    const vKey = verFail ? 'F' : 'P'
    const aKey = aliFail ? 'F' : 'P'
    const activeKey = `${iKey}${vKey}${aKey}`

    const cells = [
      { key: 'PPP', integrity: true, veracity: true, alignment: true, label: 'Verified context', description: 'Image is authentic, claim is true, and they match.', tone: 'high' },
      { key: 'PPF', integrity: true, veracity: true, alignment: false, label: 'True claim, wrong image', description: 'Authentic image with accurate claim, but they don\'t match.', tone: 'medium' },
      { key: 'PFP', integrity: true, veracity: false, alignment: true, label: 'Image supports false claim', description: 'Authentic image aligned with a false claim. Potentially dangerous.', tone: 'danger' },
      { key: 'PFF', integrity: true, veracity: false, alignment: false, label: 'False claim, wrong image', description: 'Authentic image, but claim is false and doesn\'t match.', tone: 'low' },
      { key: 'FPP', integrity: false, veracity: true, alignment: true, label: 'Tampered but aligned', description: 'Modified image supporting a true claim.', tone: 'medium' },
      { key: 'FPF', integrity: false, veracity: true, alignment: false, label: 'Tampered, true claim, mismatched', description: 'Modified image with a true claim that doesn\'t match.', tone: 'low' },
      { key: 'FFP', integrity: false, veracity: false, alignment: true, label: 'Tampered image supports false claim', description: 'Modified image aligned with a false claim. Most dangerous.', tone: 'danger' },
      { key: 'FFF', integrity: false, veracity: false, alignment: false, label: 'All signals fail', description: 'Tampered image, false claim, and they don\'t match.', tone: 'low' },
    ]

    return {
      activeKey,
      cells,
      activeCell: cells.find(c => c.key === activeKey),
      integrityUnchecked: integrity === 'unchecked' || integrity === 'addon',
    }
  }, [triangleSignals])

  const showResultsOverview = Boolean(result)
  const showProgressCard = status !== 'success'
  
  // Compute which signals were not checked
  const uncheckedSignals = useMemo(() => {
    const signals = []
    // Alignment is always checked (from synthesis)
    // Veracity is always checked (from triage)
    if (!provenanceData) signals.push('Genealogy')
    if (!orchestratorReverseSearch) signals.push('Source Reputation')
    return signals
  }, [provenanceData, orchestratorReverseSearch])
  return (
    <div className="page">
      <header className="hero">
        <div className="hero-brand">
          <div className="hero-logo-frame">
            <img
              className="hero-logo"
              src="/MedContext-banner-final.jpeg"
              alt="MedContext - Real images can mislead. We verify the claims, not just the image."
            />
          </div>
          <div>
            <p className="eyebrow">MedContext</p>
            <h1>Medical images don&apos;t need to be fake to cause harm.</h1>
            <p className="subhead">
              Check your image context with MedContext.
            </p>
          </div>
        </div>
        <div className="hero-actions">
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

      {/* Tab Toggle */}
      <nav className="tab-toggle">
        <button
          type="button"
          className={`tab-button ${activeView === 'main' || activeView === 'settings' ? 'tab-active' : ''}`}
          onClick={() => setActiveView('main')}
        >
          Verify Image
        </button>
        <button
          type="button"
          className={`tab-button ${activeView === 'validation' ? 'tab-active' : ''}`}
          onClick={() => setActiveView('validation')}
        >
          Validation Results
        </button>
      </nav>

      <main className="content">
        {activeView === 'validation' ? (
          <ValidationStory onNavigateBack={() => setActiveView('main')} />
        ) : activeView === 'settings' ? (
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
                <label className="field">
                  <span>Demo Access Code</span>
                  <input
                    type="text"
                    placeholder="Leave empty for local dev"
                    value={accessCode}
                    onChange={(event) =>
                      handleAccessCodeChange(event.target.value)
                    }
                  />
                  <span className="helper">
                    Required for public demo. See README for code.
                  </span>
                </label>
              </div>
            </div>
          </section>
        ) : (
          <>
            <div className="top-grid">
              <section
                className={[
                  'card',
                  showProgressCard || showResultsOverview ? null : 'card-span',
                ]
                  .filter(Boolean)
                  .join(' ')}
              >
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
                {(error && (error.includes('Access denied') || error.includes('403'))) || accessCode ? (
                  <label className="field">
                    <span>Demo Access Code</span>
                    <input
                      type="text"
                      placeholder="Enter access code"
                      value={accessCode}
                      onChange={(event) =>
                        handleAccessCodeChange(event.target.value)
                      }
                    />
                    <span className="helper">
                      {error && (error.includes('Access denied') || error.includes('403'))
                        ? '⚠️ Access denied. Please enter the demo access code to continue.'
                        : 'Code saved locally. Leave empty to remove.'}
                    </span>
                  </label>
                ) : null}
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
                {error && !error.includes('Access denied') && !error.includes('403') ? (
                  <p className="error">{error}</p>
                ) : null}
              </section>
              {showProgressCard ? (
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
              ) : null}
              {showResultsOverview ? (
                <section className="card triangle-card">
                  <h2>Assessment</h2>
                  <p className="helper">
                    Three-dimensional evaluation: image integrity, claim veracity, and contextual alignment.
                  </p>
                  <svg
                    className="triangle-svg"
                    viewBox="0 0 440 470"
                    role="img"
                    aria-label={`Assessment: integrity ${triangleSignals.integrity}, veracity ${triangleSignals.veracity}, alignment ${triangleSignals.alignment}`}
                  >
                    {/* Triangle edge lines */}
                    <line x1="220" y1="115" x2="75" y2="325" stroke="#c8d3de" strokeWidth="3" />
                    <line x1="220" y1="115" x2="365" y2="325" stroke="#c8d3de" strokeWidth="3" />
                    <line x1="75" y1="325" x2="365" y2="325" stroke="#c8d3de" strokeWidth="3" />

                    {/* Top vertex: Image Integrity */}
                    <text x="220" y="45" textAnchor="middle" className="tri-label-primary">Image Integrity</text>
                    <text x="220" y="62" textAnchor="middle" className="tri-label-secondary">
                      {triangleSignals.integrity === 'addon' ? '(Add-on)' : '(Forensics)'}
                    </text>
                    <circle cx="220" cy="115" r="38" className={`tri-node tri-node-${triangleSignals.integrity}`} />
                    {renderTriIcon(triangleSignals.integrity, 220, 115)}

                    {/* Bottom-left vertex: Context Veracity */}
                    <circle cx="75" cy="325" r="38" className={`tri-node tri-node-${triangleSignals.veracity}`} />
                    {renderTriIcon(triangleSignals.veracity, 75, 325)}
                    <text x="75" y="380" textAnchor="middle" className="tri-label-primary">Context</text>
                    <text x="75" y="397" textAnchor="middle" className="tri-label-primary">Veracity</text>

                    {/* Bottom-right vertex: Context-Image Alignment */}
                    <circle cx="365" cy="325" r="38" className={`tri-node tri-node-${triangleSignals.alignment}`} />
                    {renderTriIcon(triangleSignals.alignment, 365, 325)}
                    <text x="365" y="380" textAnchor="middle" className="tri-label-primary">Context-Image</text>
                    <text x="365" y="397" textAnchor="middle" className="tri-label-primary">Alignment</text>

                    {/* Overall verdict pill */}
                    <rect x="120" y="425" width="200" height="34" rx="17" className={`tri-pill tri-pill-${triangleSignals.overall}`} />
                    <text x="220" y="447" textAnchor="middle" className="tri-pill-text">Contextual Authenticity</text>
                  </svg>

                  {/* 2x2x2 Matrix */}
                  {cubeMatrix ? (
                    <div className="cube-matrix">
                      <p className="cube-matrix-title">
                        {cubeMatrix.integrityUnchecked
                          ? '2x2 assessment matrix'
                          : '2x2x2 assessment matrix'}
                      </p>
                      <div className="cube-layers">
                        {(cubeMatrix.integrityUnchecked ? [true] : [true, false]).map((intLayer) => (
                          <div key={intLayer ? 'intact' : 'tampered'} className="cube-layer">
                            {!cubeMatrix.integrityUnchecked ? (
                              <span className="cube-layer-label">
                                {intLayer ? 'Image intact' : 'Image tampered'}
                              </span>
                            ) : null}
                            <div className="cube-grid">
                              {cubeMatrix.cells
                                .filter(c => cubeMatrix.integrityUnchecked ? c.integrity : c.integrity === intLayer)
                                .map(cell => (
                                  <div
                                    key={cell.key}
                                    className={[
                                      'cube-cell',
                                      cubeMatrix.activeKey === cell.key ? `cube-active cube-${cell.tone}` : '',
                                    ].join(' ')}
                                  >
                                    <span className="cube-cell-label">{cell.label}</span>
                                  </div>
                                ))}
                            </div>
                          </div>
                        ))}
                      </div>
                      {cubeMatrix.activeCell ? (
                        <div className={`quadrant-verdict quadrant-verdict-${cubeMatrix.activeCell.tone}`}>
                          <strong>{cubeMatrix.activeCell.label}</strong>
                          <p>{cubeMatrix.activeCell.description}</p>
                        </div>
                      ) : null}
                    </div>
                  ) : assessmentQuadrant ? (
                    <div className={`quadrant-verdict quadrant-verdict-${assessmentQuadrant.tone}`}>
                      <strong>{assessmentQuadrant.title}</strong>
                      <p>{assessmentQuadrant.description}</p>
                    </div>
                  ) : null}
                </section>
              ) : null}
            </div>

            <section className="card" ref={result ? (el => el ? el.setAttribute('data-export-target', 'results') : null) : null}>
              <div className="result-header">
                <h2>Analysis Results</h2>
                {result && (
                  <div className="export-buttons">
                    <button
                      type="button"
                      className="ghost export-button"
                      onClick={() => {
                        const resultsElement = document.querySelector('[data-export-target="results"]');
                        if (resultsElement) {
                          import('./utils/exportUtils')
                            .then(async ({ downloadAsPDF }) => {
                              try {
                                await downloadAsPDF(resultsElement, 'medcontext-results.pdf');
                              } catch (error) {
                                console.error('Error in downloadAsPDF:', error);
                                alert('Failed to download PDF. Please try again.');
                              }
                            })
                            .catch((error) => {
                              console.error('Failed to load export utilities:', error);
                              alert('Failed to load export functionality. Please try again.');
                            });
                        } else {
                          alert('Results element not found for export.');
                        }
                      }}
                    >
                      Download as PDF
                    </button>
                    <button
                      type="button"
                      className="ghost export-button"
                      onClick={() => {
                        const resultsElement = document.querySelector('[data-export-target="results"]');
                        if (resultsElement) {
                          import('./utils/exportUtils')
                            .then(({ copyToClipboardText }) =>
                              copyToClipboardText(resultsElement).catch(error => {
                                console.error('Error in copyToClipboardText:', error);
                                alert('Failed to copy results to clipboard. Please try again.');
                              })
                            )
                            .catch((error) => {
                              console.error('Failed to load export utilities:', error);
                              alert('Failed to load export functionality. Please try again.');
                            });
                        } else {
                          alert('Results element not found for export.');
                        }
                      }}
                    >
                      Copy to Clipboard
                    </button>
                  </div>
                )}
              </div>
              {result ? (
                <div className="results">
                  {/* 1. Modules Selected and Their Results */}
                  <div className="result-block">
                    <h3>1. Modules Selected by Triage Agent</h3>
                    <p className="helper">
                      The triage agent selected the following analysis modules:
                    </p>

                    {/* Contextual Analysis - Always runs */}
                    <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(45, 184, 138, 0.05)', borderRadius: '8px', borderLeft: '3px solid #2db88a' }}>
                      <h4 style={{ margin: '0 0 0.5rem 0', color: '#2db88a' }}>✓ Contextual Analysis (Always Active)</h4>
                      <p className="helper">Assesses claim veracity and image-claim alignment using MedGemma.</p>
                    </div>

                    {/* Pixel Forensics */}
                    {forensicsData ? (
                      <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(78, 154, 52, 0.05)', borderRadius: '8px', borderLeft: '3px solid #4E9A34' }}>
                        <h4 style={{ margin: '0 0 0.5rem 0', color: '#4E9A34' }}>✓ Pixel Forensics Selected</h4>
                        <p className="helper" style={{ marginBottom: '1rem' }}>Detects image manipulation through pixel-level analysis.</p>
                        {forensicsData.results?.layer_1 ? (
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                            <div>
                              <strong>Verdict:</strong> <span className={`pill ${forensicsData.results.layer_1.verdict === 'AUTHENTIC' ? 'pill-success' : 'pill-error'}`}>
                                {forensicsData.results.layer_1.verdict}
                              </span>
                            </div>
                            {forensicsData.results.layer_1.confidence != null ? (
                              <div>
                                <strong>Confidence:</strong> {Math.round(forensicsData.results.layer_1.confidence * 100)}%
                              </div>
                            ) : null}
                            {forensicsData.results.layer_1.details?.copy_move_score !== undefined ? (
                              <div>
                                <strong>Copy-Move Score:</strong> {forensicsData.results.layer_1.details.copy_move_score.toFixed(4)}
                              </div>
                            ) : null}
                          </div>
                        ) : (
                          <p className="helper">Forensics analysis completed.</p>
                        )}
                      </div>
                    ) : null}

                    {/* Reverse Search */}
                    {orchestratorReverseSearch ? (
                      <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(91, 141, 239, 0.05)', borderRadius: '8px', borderLeft: '3px solid #5b8def' }}>
                        <h4 style={{ margin: '0 0 0.5rem 0', color: '#5b8def' }}>✓ Reverse Image Search Selected</h4>
                        <p className="helper" style={{ marginBottom: '1rem' }}>Finds where this image appears online.</p>
                        {orchestratorReverseSearch.matches?.length > 0 ? (
                          <div>
                            <strong>{orchestratorReverseSearch.matches.length} matches found</strong>
                            <div style={{ marginTop: '0.5rem', maxHeight: '200px', overflowY: 'auto' }}>
                              {orchestratorReverseSearch.matches.slice(0, 3).map((match, idx) => (
                                <div key={idx} style={{ marginBottom: '0.5rem', paddingBottom: '0.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                                  <div><strong>{match.title || 'Untitled'}</strong></div>
                                  {match.url ? <div style={{ fontSize: '0.85rem', opacity: 0.8 }}><a href={match.url} target="_blank" rel="noreferrer">{match.url}</a></div> : null}
                                  {match.snippet ? <div style={{ fontSize: '0.85rem', marginTop: '0.25rem' }}>{match.snippet}</div> : null}
                                </div>
                              ))}
                              {orchestratorReverseSearch.matches.length > 3 ? (
                                <div style={{ fontSize: '0.85rem', opacity: 0.7 }}>+ {orchestratorReverseSearch.matches.length - 3} more matches</div>
                              ) : null}
                            </div>
                          </div>
                        ) : (
                          <p className="helper">No matches found.</p>
                        )}
                      </div>
                    ) : null}

                    {/* Provenance */}
                    {provenanceData ? (
                      <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(245, 165, 36, 0.05)', borderRadius: '8px', borderLeft: '3px solid #f5a524' }}>
                        <h4 style={{ margin: '0 0 0.5rem 0', color: '#f5a524' }}>✓ Provenance Chain Selected</h4>
                        <p className="helper" style={{ marginBottom: '1rem' }}>Blockchain-style immutable audit trail for image history.</p>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                          <div><strong>Chain ID:</strong> <code style={{ fontSize: '0.85rem' }}>{provenanceData.chain_id?.substring(0, 16)}...</code></div>
                          <div><strong>Blocks:</strong> {provenanceData.blocks?.length || 0}</div>
                          {provenanceData.blockchain_tx_hash ? (
                            <>
                              <div style={{ gridColumn: '1 / -1' }}>
                                <strong>Blockchain Anchor:</strong> <code style={{ fontSize: '0.85rem' }}>{provenanceData.blockchain_tx_hash.substring(0, 18)}...</code>
                              </div>
                            </>
                          ) : null}
                        </div>
                      </div>
                    ) : null}

                    {!forensicsData && !orchestratorReverseSearch && !provenanceData ? (
                      <div style={{ marginTop: '1rem', padding: '1rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '8px' }}>
                        <p className="helper">Only contextual analysis was selected for this image-claim pair.</p>
                      </div>
                    ) : null}
                  </div>

                  {/* 2. Three-Dimensional Scores */}
                  <div className="result-block">
                    <h3>2. Three-Dimensional Contextual Authenticity</h3>
                    <p className="helper">
                      Each dimension is scored independently to assess different aspects of authenticity:
                    </p>
                    <div className="assessment-duo" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
                      {forensicsData ? (
                        <div className={`score-pill ${forensicsData.results?.layer_1?.verdict === 'AUTHENTIC' ? 'score-high' : 'score-low'}`}>
                          <span className="score-label">Image Integrity</span>
                          <span className="score-value-text">
                            {forensicsData.results?.layer_1?.verdict || 'Unknown'}
                          </span>
                          <span>
                            {forensicsData.results?.layer_1?.confidence != null
                              ? `${Math.round(forensicsData.results.layer_1.confidence * 100)}% confidence`
                              : 'Confidence N/A'}
                          </span>
                        </div>
                      ) : (
                        <div className="score-pill score-neutral">
                          <span className="score-label">Image Integrity</span>
                          <span className="score-value-text">Not assessed</span>
                          <span>Module not selected</span>
                        </div>
                      )}

                      {claimVeracity ? (
                        <div className={`score-pill score-${claimVeracity.tone}`}>
                          <span className="score-label">Claim Veracity</span>
                          <span className="score-value-text">
                            {claimVeracity.accuracy?.replace('_', ' ') || 'Unknown'}
                          </span>

                        </div>
                      ) : (
                        <div className="score-pill score-neutral">
                          <span className="score-label">Claim Veracity</span>
                          <span className="score-value-text">Not assessed</span>
                        </div>
                      )}

                      {alignmentScore && alignmentScore.score > 0 ? (
                        <div className={`score-pill score-${alignmentScore.tone}`}>
                          <span className="score-label">Context Alignment</span>
                          <span className="score-value">
                            {alignmentScore.score}/3
                          </span>
                          <span>{alignmentScore.label}</span>
                        </div>
                      ) : (
                        <div className="score-pill score-neutral">
                          <span className="score-label">Context Alignment</span>
                          <span className="score-value-text">Not assessed</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 3. Model Rationale */}
                  {part2 || part1 ? (
                    <div className="result-block">
                      <h3>3. Analysis Rationale</h3>
                      {imagePreview ? (
                        <img
                          className="image-preview"
                          src={imagePreview}
                          alt="Reviewed upload"
                          style={{ maxWidth: '400px', marginBottom: '1rem' }}
                        />
                      ) : null}
                      {contextQuote ? (
                        <>
                          <p className="eyebrow">
                            {isUserProvidedContext ? 'User-provided context' : 'Analyzed claim'}
                          </p>
                          <blockquote className="context-quote">
                            {contextQuote}
                          </blockquote>
                        </>
                      ) : null}
                      {part1?.image_description ? (
                        <div style={{ marginTop: '1rem' }}>
                          <p className="eyebrow">Image description</p>
                          <p className="summary-text">{part1.image_description}</p>
                        </div>
                      ) : null}
                      {part2?.summary || part2?.alignment_analysis || part2?.rationale ? (
                        <div style={{ marginTop: '1rem' }}>
                          <p className="eyebrow">Model analysis</p>
                          {part2.summary ? <p className="summary-text">{part2.summary}</p> : null}
                          {part2.alignment_analysis ? <p className="summary-text">{part2.alignment_analysis}</p> : null}
                          {part2.rationale ? <p className="summary-text">{part2.rationale}</p> : null}
                          {claimVeracity?.evidenceBasis ? (
                            <p className="summary-text"><strong>Evidence basis:</strong> {claimVeracity.evidenceBasis}</p>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                  ) : null}

                  {/* 4. Final Verdict */}
                  <div className="result-block">
                    <h3>4. Final Assessment</h3>
                    {part2?.verdict || result?.is_misinformation !== undefined ? (
                      <div className={`quadrant-verdict ${
                        result?.is_misinformation === true || part2?.verdict?.toLowerCase().includes('misinformation')
                          ? 'quadrant-verdict-danger'
                          : result?.is_misinformation === false
                            ? 'quadrant-verdict-high'
                            : 'quadrant-verdict-medium'
                      }`}>
                        <strong style={{ fontSize: '1.5rem' }}>
                          {result?.is_misinformation === true ? '⚠️ MISINFORMATION DETECTED' :
                           result?.is_misinformation === false ? '✓ NO MISINFORMATION DETECTED' :
                           part2?.verdict || 'Assessment Complete'}
                        </strong>
                        <p>
                          {part2?.verdict ? part2.verdict :
                           result?.is_misinformation === true ? 'The image-claim pair shows signs of misinformation.' :
                           result?.is_misinformation === false ? 'The image-claim pair appears authentic and aligned.' :
                           'Review the three-dimensional scores and rationale above for details.'}
                        </p>
                        {part2?.confidence ? (
                          <p style={{ marginTop: '0.5rem', opacity: 0.8 }}>
                            <strong>Confidence:</strong> {part2.confidence}
                          </p>
                        ) : null}
                      </div>
                    ) : (
                      <p className="helper">Final verdict not available</p>
                    )}
                  </div>
                </div>
              ) : (
                <p className="helper">
                  Run an analysis to see the results here.
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
                          {layerName === 'layer_1' ? '📊 Layer 1: Pixel Forensics' :
                            layerName === 'layer_2' ? '🧠 Layer 2: Semantic Analysis' :
                              '📝 Layer 3: Metadata & EXIF'}
                        </h3>
                        <div className="forensics-verdict">
                          <span className={`pill ${layerData.verdict === 'AUTHENTIC' ? 'pill-success' : layerData.verdict === 'MANIPULATED' ? 'pill-error' : 'pill-warning'}`}>
                            {layerData.verdict}
                          </span>
                          {layerData.confidence != null ? (
                            <span className="pill pill-muted">
                              {Math.round(layerData.confidence * 100)}% confidence
                            </span>
                          ) : null}
                        </div>
                        {layerData.details ? (
                          <div className="forensics-details">
                            {layerData.details.method ? (
                              <p><strong>Method:</strong> {layerData.details.method}</p>
                            ) : null}
                            {layerData.details.copy_move_score !== undefined ? (
                              <div className="forensics-stats">
                                <p><strong>Copy-Move Score:</strong> {layerData.details.copy_move_score}</p>
                                {layerData.details.image_size ? (
                                  <p><strong>Image Size:</strong> {layerData.details.image_size[0]} x {layerData.details.image_size[1]}</p>
                                ) : null}
                                {layerData.details.image_mode ? (
                                  <p><strong>Mode:</strong> {layerData.details.image_mode}</p>
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
                    {provenanceData.blockchain_tx_hash ? (
                      <p>
                        <strong>Blockchain anchor:</strong>{' '}
                        <code>{provenanceData.blockchain_tx_hash.substring(0, 18)}…</code>
                        {provenanceData.blockchain_verification_url &&
                        !provenanceData.blockchain_verification_url.startsWith('local://') ? (
                          <>
                            {' '}
                            <a
                              href={provenanceData.blockchain_verification_url}
                              target="_blank"
                              rel="noreferrer"
                              className="pill pill-success"
                            >
                              Verify on-chain ↗
                            </a>
                          </>
                        ) : null}
                      </p>
                    ) : null}
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
      <footer className="footer">
        <div className="footer-inner">
          <span>Jamie Forrest</span>
          <span className="footer-sep">•</span>
          <a href="https://drjforrest.com" target="_blank" rel="noreferrer">
            drjforrest.com
          </a>
          <span className="footer-sep">•</span>
          <a href="https://github.com/drjforrest" target="_blank" rel="noreferrer">
            GitHub
          </a>
          <span className="footer-sep">•</span>
          <a
            href="https://www.linkedin.com/in/jamie_forrest"
            target="_blank"
            rel="noreferrer"
          >
            LinkedIn
          </a>
        </div>
      </footer>
    </div>
  )
}
export default App
