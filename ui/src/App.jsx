import { useEffect, useMemo, useRef, useState } from 'react'
import AboutPage from './AboutPage'
import './App.css'
import OptimizationStory from './OptimizationStory'
import SettingsAndTools from './SettingsAndTools'
import SplashPage from './SplashPage'
import ValidationStory from './ValidationStory'
import LlamaCppStatus from './components/LlamaCppStatus'


const defaultApiBase =
  import.meta.env.VITE_API_BASE || ''
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
  const [activeView, setActiveView] = useState('landing')
  const [apiBase, setApiBase] = useState(getStoredApiBase)
  const [accessCode, setAccessCode] = useState(getStoredAccessCode)
  const [imageFile, setImageFile] = useState(null)
  const [imageUrl, setImageUrl] = useState('')
  const [context, setContext] = useState('')
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [resultTimestamp, setResultTimestamp] = useState(null)
  const [fileInputKey, setFileInputKey] = useState(0)
  const [modules, setModules] = useState(null)
  const [forceTools, setForceTools] = useState(new Set())
  const [progressPhase, setProgressPhase] = useState(0)
  const progressTimersRef = useRef([])
  const statusRef = useRef(null)
  const statusRefreshTimerRef = useRef(null)
  const [providerStatus, setProviderStatus] = useState(null)
  const [showRunModal, setShowRunModal] = useState(false)

  // Threshold configuration
  const [veracityThreshold, setVeracityThreshold] = useState(0.65)
  const [alignmentThreshold, setAlignmentThreshold] = useState(0.30)
  const [decisionLogic, setDecisionLogic] = useState('OR')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [availableModels, setAvailableModels] = useState([])
  const [selectedModel, setSelectedModel] = useState('')
  const [selectionStatus, setSelectionStatus] = useState('')

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

  // Fetch available models on mount and when API base changes
  const fetchModels = async () => {
    try {
      const headers = {}
      if (accessCode.trim()) {
        headers['X-Demo-Access-Code'] = accessCode.trim()
      }
      const res = await fetch(
        `${apiBase.replace(/\/$/, '')}/api/v1/orchestrator/providers`,
        { headers },
      )
      if (res.ok) {
        const data = await res.json()
        setAvailableModels(data)
        // Set default selected model to the first available one that is actually available
        if (!selectedModel && data.length > 0) {
          const defaultModel = data.find(m => m.available) || data[0]
          setSelectedModel(defaultModel.model)
        }
      }
    } catch (err) {
      console.error('Failed to fetch models:', err)
    }
  }

  useEffect(() => {
    fetchModels()
  }, [apiBase, accessCode])

  // Update thresholds when selected model changes
  useEffect(() => {
    if (selectedModel && availableModels.length > 0) {
      const modelInfo = availableModels.find(m => m.model === selectedModel)
      if (modelInfo) {
        if (modelInfo.recommended_veracity_threshold !== undefined) {
          setVeracityThreshold(modelInfo.recommended_veracity_threshold)
        }
        if (modelInfo.recommended_alignment_threshold !== undefined) {
          setAlignmentThreshold(modelInfo.recommended_alignment_threshold)
        }
        if (modelInfo.recommended_decision_logic !== undefined) {
          setDecisionLogic(modelInfo.recommended_decision_logic)
        }
        
        // Add feedback for user
        if (modelInfo.available) {
          setSelectionStatus(`✅ ${modelInfo.name} available. Optimized thresholds loaded.`)
        } else {
          setSelectionStatus(`❌ ${modelInfo.name} is currently unavailable.`)
        }
        
        // Clear message after 5 seconds
        const timer = setTimeout(() => {
          setSelectionStatus('')
        }, 5000)
        return () => clearTimeout(timer)
      }
    }
  }, [selectedModel, availableModels])

  const handleModelSelect = (model) => {
    setSelectedModel(model)
    setSelectionStatus('⏳ Verifying model availability...')
    fetchModels()
  }

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

  // Progressive animation: stagger module activation for visual feedback
  useEffect(() => {
    progressTimersRef.current.forEach(clearTimeout)
    progressTimersRef.current = []

    if (status === 'loading') {
      setProgressPhase(1)                                        // veracity → active
      const t1 = setTimeout(() => setProgressPhase(2), 5000)   // veracity "done" after 5s
      const t2 = setTimeout(() => setProgressPhase(3), 7000)   // alignment → active after 2s pause
      const t3 = setTimeout(() => setProgressPhase(4), 12000)  // add-ons → awaiting
      progressTimersRef.current = [t1, t2, t3]
    } else if (status === 'success') {
      setProgressPhase(5)
      const t4 = setTimeout(() => setProgressPhase(6), 500)
      const t5 = setTimeout(() => setProgressPhase(7), 1500)
      progressTimersRef.current = [t4, t5]
    } else if (status === 'error') {
      setProgressPhase(-1)
    } else if (status === 'idle') {
      setProgressPhase(0)
    }

    return () => {
      progressTimersRef.current.forEach(clearTimeout)
      progressTimersRef.current = []
    }
  }, [status])

  const agentSteps = [
    {
      key: 'claim_veracity',
      label: 'Claim Veracity',
      detail: 'Assesses factual accuracy of the claim against medical knowledge.',
      toolKey: null,
      isCore: true,
      isHalfWidth: true,
    },
    {
      key: 'context_alignment',
      label: 'Image-Context Alignment',
      detail: 'Evaluates whether the image supports the associated claim.',
      toolKey: null,
      isCore: true,
      isHalfWidth: true,
    },
    {
      key: 'image_integrity',
      label: 'Image Integrity',
      detail: 'Pixel forensics, metadata, and manipulation detection.',
      toolKey: 'forensics',
      isCore: false,
    },
    {
      key: 'source_verification',
      label: 'Source Verification',
      detail: 'Reverse image search to find where this image appears online.',
      toolKey: 'reverse_search',
      isCore: false,
    },
    {
      key: 'provenance',
      label: 'Provenance',
      detail: 'Immutable audit trail and usage history for the image.',
      toolKey: 'provenance',
      isCore: false,
    },
    {
      key: 'synthesis',
      label: 'Synthesis Agent',
      detail: 'Combines all signals into a final contextual authenticity verdict.',
      toolKey: null,
      isCore: false,
      isSynthesis: true,
    },
  ]

  // handleRun: validate inputs, then show the confirmation modal
  const handleRun = () => {
    setError('')

    // Block if local model is busy
    if (llamaCppBusy) {
      setError(
        'Local AI is currently processing a request. ' +
        'The local model handles one request at a time — please wait 2–3 minutes and try again.'
      )
      setStatus('error')
      return
    }

    if ((hasFile && hasUrl) || (!hasFile && !hasUrl)) {
      setError('Provide either an image file or a public image URL.')
      setStatus('error')
      return
    }

    if (!context.trim()) {
      setError('Clinical context is required to evaluate the image.')
      setStatus('error')
      return
    }

    // Inputs look good — show the confirmation modal
    setShowRunModal(true)
  }

  // handleConfirmRun: called when the user confirms in the modal
  const handleConfirmRun = async () => {
    setShowRunModal(false)
    setResult(null)
    setResultTimestamp(null)
    setProgressPhase(0)

    // Immediately refresh provider status so the navbar chip reflects "busy"
    statusRef.current?.refresh()

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
    if (forceTools.size > 0) {
      formData.append('force_tools', Array.from(forceTools).join(','))
    }

    // Add threshold configuration
    formData.append('veracity_threshold', veracityThreshold.toString())
    formData.append('alignment_threshold', alignmentThreshold.toString())
    formData.append('decision_logic', decisionLogic)
    if (selectedModel) {
      formData.append('medgemma_model', selectedModel)
    }

    setStatus('loading')
    // Refresh status after a short delay so the backend has registered the request
    const timerId = setTimeout(() => statusRef.current?.refresh(), 500)
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
      setResultTimestamp(Date.now())
      setStatus('success')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Request failed.')
      setStatus('error')
    } finally {
      clearTimeout(timerId)
    }
    // Refresh status so chip returns to idle promptly
    statusRef.current?.refresh()
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
  const thresholdRecommendation = result?.triage?.threshold_recommendation
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
      if (progressPhase === 0) return 'idle'

      // Error state: all steps that were pending/active become 'error'
      if (progressPhase === -1) {
        // Core steps and synthesis all failed
        if (step.isCore || step.isSynthesis) return 'error'
        return 'skipped'
      }

      // Claim Veracity: active at phase 1, simulated-done at phase 2+ (before result), actual-done at 5+
      if (step.key === 'claim_veracity') {
        if (progressPhase >= 5) return 'done'
        if (progressPhase >= 2) return 'done'  // simulated: veracity analyzed, alignment starting
        if (progressPhase >= 1) return 'active'
        return 'pending'
      }

      // Image-Context Alignment: activates at phase 3 (after veracity "done"), done at 5+
      if (step.key === 'context_alignment') {
        if (progressPhase >= 5) return 'done'
        if (progressPhase >= 3) return 'active'
        return 'pending'
      }

      // Synthesis: active at phase 6, done at phase 7
      if (step.isSynthesis) {
        if (progressPhase >= 7) return 'done'
        if (progressPhase >= 6) return 'active'
        if (progressPhase >= 5) return 'pending'
        return 'idle'
      }

      // Add-on modules: awaiting at phase 4, resolve at phase 5+
      if (progressPhase >= 5) {
        return toolActivity[step.toolKey] ? 'done' : 'skipped'
      }
      if (progressPhase >= 4) {
        return forceTools.has(step.toolKey) ? 'active' : 'awaiting'
      }
      return 'pending'
    })
  }, [agentSteps, progressPhase, toolActivity, forceTools])
  const claimVeracity = useMemo(() => {
    const veracity =
      part2?.claim_veracity || contextualIntegrity?.claim_veracity || null
    if (!veracity || typeof veracity !== 'object') {
      // Check if there's a direct accuracy string in part2 or contextualIntegrity
      const directAccuracy = part2?.accuracy || contextualIntegrity?.accuracy || 
                            (typeof part2 === 'string' ? part2 : null)
      if (directAccuracy && typeof directAccuracy === 'string') {
        const accuracy = directAccuracy.toLowerCase()
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
          evidenceBasis: null,
          publicHealthContext: null,
        }
      }
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
  }, [part2?.claim_veracity, contextualIntegrity?.claim_veracity, part2?.accuracy, contextualIntegrity?.accuracy, part2])
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

    const getProvenanceStatus = () => {
      if (!isAddonEnabled('provenance')) return 'addon'
      if (!provenanceData) return 'unchecked'
      if (provenanceData.status === 'completed' && (provenanceData.blocks?.length > 0)) return 'pass'
      return 'unchecked'
    }

    const getSourceStatus = () => {
      if (!isAddonEnabled('reverse_search')) return 'addon'
      if (!orchestratorReverseSearch) return 'unchecked'
      if (orchestratorReverseSearch.matches) return 'pass'
      return 'unchecked'
    }

    const integrity = getForensicsStatus()
    const veracity = getVeracityStatus()
    const alignment = getAlignmentStatus()
    const provenance = getProvenanceStatus()
    const source = getSourceStatus()

    const checked = [veracity, alignment].filter(s => s !== 'unchecked' && s !== 'addon')
    let overall = 'unchecked'
    if (checked.length > 0) {
      if (checked.every(s => s === 'pass')) overall = 'pass'
      else if (checked.some(s => s === 'fail')) overall = 'fail'
      else overall = 'partial'
    }

    return { integrity, veracity, alignment, provenance, source, overall }
  }, [forensicsData, claimVeracity, alignmentScore, provenanceData, orchestratorReverseSearch])

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
  const showProgressCard = status !== 'success' || progressPhase < 7
  
  const isLanding = activeView === 'landing'

  const llamaCppBusy = providerStatus?.active_provider === 'llama_cpp' && providerStatus?.busy === true

  return (
    <div className="page">
      {!isLanding && (
        <nav className="tab-bar">
          <button
            type="button"
            className="tab-button tab-button--home"
            onClick={() => setActiveView('landing')}
            aria-label="Home"
          >
            Home
          </button>
          <button
            type="button"
            className={`tab-button ${activeView === 'main' ? 'tab-active' : ''}`}
            onClick={() => setActiveView('main')}
          >
            Verification
          </button>
          <button
            type="button"
            className={`tab-button ${activeView === 'validation' ? 'tab-active' : ''}`}
            onClick={() => setActiveView('validation')}
          >
            Validation
          </button>
          <button
            type="button"
            className={`tab-button ${activeView === 'optimization' ? 'tab-active' : ''}`}
            onClick={() => setActiveView('optimization')}
          >
            Optimization
          </button>
          <button
            type="button"
            className={`tab-button ${activeView === 'settings' ? 'tab-active' : ''}`}
            onClick={() => setActiveView('settings')}
          >
            Settings & Tools
          </button>
          <button
            type="button"
            className={`tab-button ${activeView === 'about' ? 'tab-active' : ''}`}
            onClick={() => setActiveView('about')}
          >
            About
          </button>
          {/* Provider status chip — always visible in the nav bar */}
          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', paddingRight: '0.5rem' }}>
            <LlamaCppStatus
              ref={statusRef}
              apiBase={apiBase}
              accessCode={accessCode}
              onStatusChange={setProviderStatus}
            />
          </div>
        </nav>
      )}

      <main className="content">
        {isLanding ? (
          <SplashPage
            onNavigateToVerify={() => setActiveView('main')}
            onNavigateToValidation={() => setActiveView('validation')}
          />
        ) : activeView === 'validation' ? (
          <ValidationStory />
        ) : activeView === 'optimization' ? (
          <OptimizationStory />
        ) : activeView === 'about' ? (
          <AboutPage />
        ) : activeView === 'settings' ? (
          <SettingsAndTools
            apiBase={apiBase}
            accessCode={accessCode}
            onApiBaseChange={handleApiBaseChange}
            onAccessCodeChange={handleAccessCodeChange}
            defaultApiBase={defaultApiBase}
            availableModels={availableModels}
            selectedModel={selectedModel}
            onModelSelect={handleModelSelect}
          />
        ) : (
          <>
            <section className="card" style={{ padding: 0, overflow: 'hidden' }}>
              <img
                className="page-banner"
                src="/images/main-app-banner.png"
                alt="MedContext - Real images can mislead. We verify the claims, not just the image."
              />
              <div className="page-header">
                <p className="eyebrow">MedContext</p>
                <h1>Medical images don&apos;t need to be fake to cause harm.</h1>
                <p className="subhead">
                  Check your image context with MedContext.
                </p>
              </div>
            </section>
            <div className="top-grid">
              <section
                className={[
                  'card input-card',
                  showProgressCard || showResultsOverview ? null : 'card-span',
                ]
                  .filter(Boolean)
                  .join(' ')}
              >
                <div className="input-card-header">
                  <h2>Verify an Image</h2>
                  <div className="inline-status" aria-live="polite">
                    <span className={`status-dot status-${status}`} />
                    {status === 'loading' ? (
                      <span className="spinner" aria-hidden="true" />
                    ) : null}
                    <span>{statusLabel}</span>
                  </div>
                </div>

                {/* ── Image input sub-card ─────────────────────────── */}
                <div className="input-subcard">
                  <p className="input-subcard-label">Image</p>
                  <label className="field">
                    <span>Upload a file</span>
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

                  <div className="input-or-divider"><span>or</span></div>

                  <label className="field">
                    <span>Public image URL</span>
                    <input
                      type="url"
                      placeholder="https://example.com/image.jpg"
                      value={imageUrl}
                      onChange={(event) => setImageUrl(event.target.value)}
                    />
                    <span className="helper">Use a direct image link if possible.</span>
                  </label>
                </div>

                {/* ── Clinical context sub-card (grows to fill remaining height) ── */}
                <div className="input-subcard input-subcard--grow">
                  <p className="input-subcard-label">Claim / Context</p>
                  <label className="field field--flex">
                    <span>
                      Clinical context{' '}
                      <span style={{ fontWeight: 400, color: 'var(--error)' }}>*</span>
                    </span>
                    <textarea
                      placeholder="Caption or claim about the image — e.g. 'This X-ray shows signs of tuberculosis in a 30-year-old'"
                      value={context}
                      onChange={(event) => setContext(event.target.value)}
                      required
                    />
                    <span className="helper">
                      Provide the medical claim or context exactly as it appeared.
                    </span>
                  </label>
                </div>
                
                {/* ── Advanced Settings sub-card ─────────────────────── */}
                <div className="input-subcard advanced-settings">
                  <button
                    type="button"
                    className="advanced-toggle"
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    aria-expanded={showAdvanced}
                  >
                    <span className="input-subcard-label">Advanced Settings</span>
                    <span className="advanced-chevron" aria-hidden="true">
                      {showAdvanced ? '▾' : '▸'}
                    </span>
                  </button>

                  {showAdvanced && (
                    <div className="advanced-panel">
                      {/* Decision Thresholds */}
                      <div className="advanced-section">
                        <p className="advanced-section-title">Decision Thresholds</p>
                        <p className="helper">
                          Optimized defaults: veracity &lt; 0.65 OR alignment &lt; 0.30 (Med-MMHL).
                          Current logic: <strong>{decisionLogic}</strong>.
                        </p>
                        <div className="advanced-threshold-grid">
                          <label className="advanced-field">
                            <span>Veracity Threshold</span>
                            <input
                              type="range"
                              min="0" max="1" step="0.05"
                              value={veracityThreshold}
                              onChange={(e) => {
                                const parsed = parseFloat(e.target.value)
                                setVeracityThreshold(isNaN(parsed) ? veracityThreshold : parsed)
                              }}
                              className="advanced-range"
                            />
                            <input
                              type="number"
                              min="0" max="1" step="0.05"
                              value={veracityThreshold}
                              onChange={(e) => {
                                const parsed = parseFloat(e.target.value)
                                setVeracityThreshold(isNaN(parsed) ? veracityThreshold : parsed)
                              }}
                              className="advanced-number"
                            />
                          </label>
                          <label className="advanced-field">
                            <span>Alignment Threshold</span>
                            <input
                              type="range"
                              min="0" max="1" step="0.05"
                              value={alignmentThreshold}
                              onChange={(e) => {
                                const parsed = parseFloat(e.target.value)
                                setAlignmentThreshold(isNaN(parsed) ? alignmentThreshold : parsed)
                              }}
                              className="advanced-range"
                            />
                            <input
                              type="number"
                              min="0" max="1" step="0.05"
                              value={alignmentThreshold}
                              onChange={(e) => {
                                const parsed = parseFloat(e.target.value)
                                setAlignmentThreshold(isNaN(parsed) ? alignmentThreshold : parsed)
                              }}
                              className="advanced-number"
                            />
                          </label>
                        </div>
                        <label className="advanced-field">
                          <span>Decision Logic</span>
                          <select
                            value={decisionLogic}
                            onChange={(e) => setDecisionLogic(e.target.value)}
                            className="advanced-select"
                          >
                            <option value="OR">OR — Flag if veracity OR alignment below threshold (high recall)</option>
                            <option value="AND">AND — Flag if veracity AND alignment below threshold (high precision)</option>
                            <option value="MIN">MIN — Flag if minimum of both below threshold (balanced)</option>
                          </select>
                        </label>
                      </div>

                      {/* Module Overrides */}
                      {['forensics', 'reverse_search', 'provenance'].some(isAddonEnabled) && (
                        <div className="advanced-section">
                          <p className="advanced-section-title">Module Overrides</p>
                          <p className="helper">Force-run specific modules regardless of triage decision.</p>
                          <div className="advanced-checkboxes">
                            {[
                              { key: 'forensics', label: 'Image Integrity (Pixel Forensics)' },
                              { key: 'reverse_search', label: 'Source Verification (reverse image search)' },
                              { key: 'provenance', label: 'Provenance (audit trail)' },
                            ]
                              .filter(({ key }) => isAddonEnabled(key))
                              .map(({ key, label }) => (
                                <label key={key} className="advanced-checkbox-label">
                                  <input
                                    type="checkbox"
                                    checked={forceTools.has(key)}
                                    onChange={(e) => {
                                      setForceTools((prev) => {
                                        const next = new Set(prev)
                                        if (e.target.checked) next.add(key)
                                        else next.delete(key)
                                        return next
                                      })
                                    }}
                                    className="advanced-checkbox"
                                  />
                                  {label}
                                </label>
                              ))}
                          </div>
                        </div>
                      )}

                      <p className="advanced-tip">
                        Use <strong>Settings &amp; Tools</strong> to find optimal threshold values for your model and dataset.
                      </p>
                    </div>
                  )}
                </div>

                {/* Demo Access Code — appears only when needed */}
                {(error && (error.includes('Access denied') || error.includes('403'))) || accessCode ? (
                  <label className="field">
                    <span>Demo Access Code</span>
                    <input
                      type="text"
                      placeholder="Enter access code"
                      value={accessCode}
                      onChange={(event) => handleAccessCodeChange(event.target.value)}
                    />
                    <span className="helper">
                      {error && (error.includes('Access denied') || error.includes('403'))
                        ? 'Access denied. Please enter the demo access code to continue.'
                        : 'Code saved locally. Leave empty to remove.'}
                    </span>
                  </label>
                ) : null}

                {/* Local AI busy warning */}
                {llamaCppBusy && (
                  <div className="busy-warning">
                    <span className="busy-warning-icon" aria-hidden="true">⏳</span>
                    <div>
                      <strong>Local AI is processing a request</strong>
                      <p className="helper">The local model handles one request at a time. Please wait 2–3 minutes before submitting.</p>
                    </div>
                  </div>
                )}

                <div className="actions">
                  <button
                    type="button"
                    onClick={handleRun}
                    disabled={status === 'loading' || llamaCppBusy}
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
                      setResultTimestamp(null)
                      setError('')
                      setStatus('idle')
                      setForceTools(new Set())
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
                      <h2>Analysis Pipeline</h2>
                      <p className="helper">
                        {status === 'loading'
                          ? 'Module selection and analysis in progress...'
                          : 'All modules complete.'}
                      </p>
                    </div>
                  </div>
                  <div className="activity-grid">
                    {agentSteps.map((step, index) => {
                      const state = agentStepStates[index]
                      const stateLabels = {
                        idle: 'Not started',
                        pending: step.isSynthesis ? 'Queued' : 'Pending',
                        awaiting: 'Awaiting agent',
                        active: step.isCore ? 'Analyzing...' : step.isSynthesis ? 'Synthesizing...' : 'Running...',
                        done: 'Complete',
                        skipped: 'Not selected',
                        error: 'Failed',
                      }
                      const stepClass = [
                        'activity-step',
                        `activity-${state}`,
                        step.isHalfWidth ? 'activity-half' : '',
                        step.isCore ? 'activity-core' : '',
                        step.isSynthesis ? 'activity-synthesis' : '',
                      ].filter(Boolean).join(' ')
                      return (
                        <div className={stepClass} key={step.key}>
                          <div className="activity-header">
                            <span>
                              {step.label}
                              {step.isCore && (
                                <span className="badge-core">Core</span>
                              )}
                              {step.isSynthesis && (
                                <span className="badge-final">Final</span>
                              )}
                            </span>
                            <span className={`activity-pill activity-${state}`}>
                              {state === 'active' && '⏳ '}
                              {state === 'awaiting' && '… '}
                              {state === 'done' && '✓ '}
                              {state === 'error' && '✗ '}
                              {state === 'skipped' && '○ '}
                              {stateLabels[state] || state}
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
                <section className="card signal-overview-card">
                  <h2>Assessment Overview</h2>

                  {/* Core signal blocks: Veracity + Alignment side by side */}
                  <div className="signal-core-grid">
                    {/* Veracity */}
                    <div className={`signal-block signal-block-veracity${triangleSignals ? ` signal-${triangleSignals.veracity}` : ''}`}>
                      <div className="signal-block-top">
                        <span className="signal-block-name">Claim Veracity</span>
                        <span className={`signal-block-badge signal-tone-${claimVeracity?.tone || 'neutral'}`}>
                          {claimVeracity?.tone === 'high' ? '✓' : claimVeracity?.tone === 'low' ? '✗' : claimVeracity?.tone === 'medium' ? '△' : '—'}
                        </span>
                      </div>
                      <p className="signal-block-label">
                        {claimVeracity?.label || 'Not assessed'}
                      </p>
                      <p className="signal-block-detail">
                        {claimVeracity?.evidenceBasis || 'Factual accuracy of the medical claim'}
                      </p>
                    </div>

                    {/* Alignment */}
                    <div className={`signal-block signal-block-alignment${triangleSignals ? ` signal-${triangleSignals.alignment}` : ''}`}>
                      <div className="signal-block-top">
                        <span className="signal-block-name">Image-Context Alignment</span>
                        <span className={`signal-block-badge signal-tone-${alignmentScore?.tone || 'neutral'}`}>
                          {alignmentScore?.tone === 'high' ? '✓' : alignmentScore?.tone === 'low' ? '✗' : alignmentScore?.tone === 'medium' ? '△' : '—'}
                        </span>
                      </div>
                      <p className="signal-block-label">
                        {alignmentScore?.label || 'Not assessed'}
                      </p>
                      <p className="signal-block-detail">
                        Whether the image supports the associated claim
                      </p>
                    </div>
                  </div>

                  {/* Verdict panel */}
                  {assessmentQuadrant ? (
                    <div className={`signal-verdict signal-verdict-${assessmentQuadrant.tone}`}>
                      <span className="signal-verdict-icon" aria-hidden="true">
                        {assessmentQuadrant.tone === 'high' ? '✓' : assessmentQuadrant.tone === 'danger' ? '⚠' : '△'}
                      </span>
                      <div>
                        <strong>{assessmentQuadrant.title}</strong>
                        <p>{assessmentQuadrant.description}</p>
                      </div>
                    </div>
                  ) : result?.is_misinformation != null ? (
                    <div className={`signal-verdict signal-verdict-${result.is_misinformation ? 'danger' : 'high'}`}>
                      <span className="signal-verdict-icon" aria-hidden="true">
                        {result.is_misinformation ? '⚠' : '✓'}
                      </span>
                      <div>
                        <strong>{result.is_misinformation ? 'Misinformation detected' : 'Context appears authentic'}</strong>
                        <p>{result.is_misinformation
                          ? 'The claim does not align with the image or contains factual inaccuracies.'
                          : 'No significant contextual integrity issues detected.'}</p>
                      </div>
                    </div>
                  ) : null}

                  {/* Add-on signal chips */}
                  {triangleSignals && (
                    <div className="signal-addon-row">
                      <div className={`signal-chip signal-chip-${triangleSignals.integrity}`}>
                        <span className="signal-chip-dot" aria-hidden="true" />
                        <span>Image Integrity</span>
                      </div>
                      <div className={`signal-chip signal-chip-${triangleSignals.source}`}>
                        <span className="signal-chip-dot" aria-hidden="true" />
                        <span>Source Verification</span>
                      </div>
                      <div className={`signal-chip signal-chip-${triangleSignals.provenance}`}>
                        <span className="signal-chip-dot" aria-hidden="true" />
                        <span>Provenance</span>
                      </div>
                    </div>
                  )}
                </section>
              ) : null}
            </div>

            {/* Results: 7 focused cards, rendered after analysis completes */}
            {result && (
              <div data-export-target="results" className="results-stack">

                {/* Results header: timestamp + export actions */}
                <div className="results-header">
                  <div>
                    <h2 style={{ margin: 0 }}>Analysis Results</h2>
                    <p className="helper" style={{ marginTop: '0.25rem' }}>
                      {resultTimestamp ? new Date(resultTimestamp).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' }) : new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}
                      {' '}at{' '}
                      {resultTimestamp ? new Date(resultTimestamp).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  <div className="export-buttons">
                    <button
                      type="button"
                      className="ghost export-button"
                      onClick={() => {
                        const el = document.querySelector('[data-export-target="results"]');
                        if (el) {
                          import('./utils/exportUtils')
                            .then(async ({ downloadAsPDF }) => {
                              try { await downloadAsPDF(el, 'medcontext-results.pdf'); }
                              catch { alert('Failed to download PDF. Please try again.'); }
                            })
                            .catch(() => alert('Failed to load export functionality. Please try again.'));
                        }
                      }}
                    >
                      Download as PDF
                    </button>
                    <button
                      type="button"
                      className="ghost export-button"
                      onClick={() => {
                        const el = document.querySelector('[data-export-target="results"]');
                        if (el) {
                          import('./utils/exportUtils')
                            .then(({ copyToClipboardText }) =>
                              copyToClipboardText(el).catch(() =>
                                alert('Failed to copy results to clipboard. Please try again.')
                              )
                            )
                            .catch(() => alert('Failed to load export functionality. Please try again.'));
                        }
                      }}
                    >
                      Copy to Clipboard
                    </button>
                  </div>
                </div>

                {/* Card 1: Submitted Image & Claim */}
                {(imagePreview || contextQuote || part1?.image_description) && (
                  <section className="card">
                    <h2>Submitted Image &amp; Claim</h2>
                    {imagePreview && (
                      <img
                        className="image-preview"
                        src={imagePreview}
                        alt="Reviewed upload"
                        style={{ maxWidth: '400px', borderRadius: '8px' }}
                      />
                    )}
                    {contextQuote && (
                      <>
                        <p className="eyebrow" style={{ marginTop: '1rem' }}>
                          {isUserProvidedContext ? 'User-provided context' : 'Analyzed claim'}
                        </p>
                        <blockquote className="context-quote">{contextQuote}</blockquote>
                      </>
                    )}
                    {part1?.image_description && (
                      <div style={{ marginTop: '1rem' }}>
                        <p className="eyebrow">Image description (MedGemma)</p>
                        <p className="summary-text">{part1.image_description}</p>
                      </div>
                    )}
                  </section>
                )}

                {/* Card 2: Verdict */}
                <section className="card">
                  <h2>Verdict</h2>
                  {thresholdRecommendation && (
                    <div style={{
                      background: 'rgba(245, 165, 36, 0.1)',
                      border: '2px solid #f5a524',
                      borderRadius: '12px',
                      padding: '1.25rem',
                      marginTop: '1rem',
                    }}>
                      <h3 style={{ color: '#f5a524', marginTop: 0 }}>Threshold Optimization Recommended</h3>
                      <p style={{ lineHeight: '1.6', marginBottom: '1rem' }}>{thresholdRecommendation.message}</p>
                      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
                        <button
                          onClick={() => setActiveView('settings')}
                          style={{
                            padding: '0.6rem 1.25rem',
                            background: '#c85a00',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '8px',
                            fontWeight: 600,
                            cursor: 'pointer',
                          }}
                        >
                          {thresholdRecommendation.action}
                        </button>
                        <span style={{ fontSize: '0.9rem', color: 'var(--muted)' }}>
                          {thresholdRecommendation.benefit}
                        </span>
                      </div>
                    </div>
                  )}
                  <div style={{ marginTop: '1.25rem' }}>
                    {part2?.verdict || result?.is_misinformation !== undefined ? (
                      <div className={`quadrant-verdict ${
                        result?.is_misinformation === true || part2?.verdict?.toLowerCase().includes('misinformation')
                          ? 'quadrant-verdict-danger'
                          : result?.is_misinformation === false
                            ? 'quadrant-verdict-high'
                            : 'quadrant-verdict-medium'
                      }`}>
                        <strong style={{ fontSize: '1.8rem', display: 'block', marginBottom: '0.5rem' }}>
                          {result?.is_misinformation === true ? 'MISINFORMATION DETECTED' :
                           result?.is_misinformation === false ? 'NO MISINFORMATION DETECTED' :
                           part2?.verdict || 'Assessment Complete'}
                        </strong>
                        <p style={{ fontSize: '1.1rem' }}>
                          {result?.is_misinformation === true
                            ? 'This image-claim combination shows signs of contextual misinformation.'
                            : result?.is_misinformation === false
                              ? 'No contextual misinformation detected.'
                              : (part2?.verdict || 'Review the contextual authenticity scores below.')}
                        </p>
                        {part2?.confidence && (
                          <p style={{ marginTop: '0.75rem', opacity: 0.85 }}>
                            <strong>Confidence:</strong> {part2.confidence}
                          </p>
                        )}
                      </div>
                    ) : (
                      <p className="helper">Final verdict not available.</p>
                    )}
                  </div>
                </section>

                {/* Card 3: Analysis Narrative */}
                {(part2?.summary || part2?.alignment_analysis || part2?.rationale || claimVeracity?.evidenceBasis) && (
                  <section className="card">
                    <h2>Analysis Narrative</h2>
                    <p className="helper">How the model arrived at its verdict:</p>
                    <div style={{ marginTop: '1rem' }}>
                      {part2?.summary && <p className="summary-text">{part2.summary}</p>}
                      {part2?.alignment_analysis && (
                        <div style={{ marginTop: '0.75rem' }}>
                          <p className="eyebrow">Alignment Analysis</p>
                          <p className="summary-text">{part2.alignment_analysis}</p>
                        </div>
                      )}
                      {part2?.rationale && (
                        <div style={{ marginTop: '0.75rem' }}>
                          <p className="eyebrow">Rationale</p>
                          <p className="summary-text">{part2.rationale}</p>
                        </div>
                      )}
                      {claimVeracity?.evidenceBasis && (
                        <div style={{ marginTop: '0.75rem' }}>
                          <p className="eyebrow">Evidence Basis</p>
                          <p className="summary-text">{claimVeracity.evidenceBasis}</p>
                        </div>
                      )}
                    </div>
                  </section>
                )}

                {/* Card 4: Contextual Authenticity — colour-coded by signal */}
                <section className="card">
                  <h2>Contextual Authenticity</h2>
                  <p className="helper">
                    Combining claim veracity with image-context alignment — the core MedContext signal for detecting misinformation.
                  </p>
                  <div className="ca-score-grid">
                    {/* Veracity — red */}
                    <div
                      className="ca-score-block"
                      style={claimVeracity
                        ? { '--ca-color': '#E63946', '--ca-bg': 'rgba(230,57,70,0.1)', '--ca-border': 'rgba(230,57,70,0.3)' }
                        : { '--ca-color': 'var(--muted)', '--ca-bg': 'var(--surface-muted)', '--ca-border': 'var(--border)' }
                      }
                    >
                      <span className="ca-score-label">Claim Veracity</span>
                      <span className="ca-score-value">
                        {claimVeracity ? (claimVeracity.accuracy?.replace('_', ' ') || 'Unknown') : 'Not assessed'}
                      </span>
                      {claimVeracity?.label && <span className="ca-score-sublabel">{claimVeracity.label}</span>}
                    </div>

                    {/* Alignment — amber */}
                    <div
                      className="ca-score-block"
                      style={alignmentScore && alignmentScore.score > 0
                        ? { '--ca-color': '#F4A261', '--ca-bg': 'rgba(244,162,97,0.1)', '--ca-border': 'rgba(244,162,97,0.3)' }
                        : { '--ca-color': 'var(--muted)', '--ca-bg': 'var(--surface-muted)', '--ca-border': 'var(--border)' }
                      }
                    >
                      <span className="ca-score-label">Context-Image Alignment</span>
                      <span className="ca-score-value">
                        {alignmentScore && alignmentScore.score > 0 ? `${alignmentScore.score}/3` : 'Not assessed'}
                      </span>
                      {alignmentScore?.label && alignmentScore.score > 0 && (
                        <span className="ca-score-sublabel">{alignmentScore.label}</span>
                      )}
                    </div>

                    {/* Combined — teal */}
                    <div
                      className="ca-score-block ca-score-block--wide"
                      style={{ '--ca-color': '#2A9D8F', '--ca-bg': 'rgba(42,157,143,0.1)', '--ca-border': 'rgba(42,157,143,0.3)' }}
                    >
                      <span className="ca-score-label">Combined Assessment</span>
                      <span className="ca-score-value">
                        {result?.is_misinformation === true ? 'Misinformation' :
                         result?.is_misinformation === false ? 'Authentic' :
                         part2?.verdict || 'Pending'}
                      </span>
                      {assessmentQuadrant?.title && (
                        <span className="ca-score-sublabel">{assessmentQuadrant.title}</span>
                      )}
                    </div>
                  </div>
                </section>

                {/* Card 5: Image Integrity (Pixel Forensics) — add-on */}
                <section className="card">
                  <h2>Image Integrity</h2>
                  <p className="helper">
                    Pixel-level forensics for detecting image manipulation. Optional add-on, separate from contextual authenticity.
                  </p>
                  <div style={{ marginTop: '1rem' }}>
                    <div className="score-pill score-neutral">
                      <span className="score-label">Image Integrity</span>
                      <span className="score-value-text">Not assessed</span>
                      <span>{isAddonEnabled('forensics') ? 'Module not selected by triage agent' : 'Add-on module disabled'}</span>
                    </div>
                  </div>
                </section>

                {/* Card 6: Source Verification — always shown */}
                <section className="card">
                  <h2>Source Verification</h2>
                  <p className="helper">
                    Reverse image search to find where this image appears online and check for context discrepancies.
                  </p>
                  {orchestratorReverseSearch ? (
                    <div style={{ marginTop: '1rem' }}>
                      <div className="reverse-meta" style={{ marginBottom: '1rem' }}>
                        {orchestratorReverseSearch.image_id && (
                          <span>Image ID: {orchestratorReverseSearch.image_id}</span>
                        )}
                        {orchestratorReverseSearch.query_hash && (
                          <span>Query Hash: {orchestratorReverseSearch.query_hash}</span>
                        )}
                      </div>
                      {orchestratorReverseSearch.matches?.length > 0 ? (
                        <div className="match-grid">
                          {orchestratorReverseSearch.matches.map((match, idx) => (
                            <article className="match-card" key={idx}>
                              <div className="match-header">
                                <span className="pill">{match.source || 'Unknown'}</span>
                                {match.confidence && (
                                  <span className="pill pill-muted">
                                    {Math.round(match.confidence * 100)}% confidence
                                  </span>
                                )}
                              </div>
                              <h3>{match.title || 'Untitled match'}</h3>
                              {match.snippet && <p className="summary-text">{match.snippet}</p>}
                              {match.url && (
                                <a href={match.url} target="_blank" rel="noreferrer">{match.url}</a>
                              )}
                            </article>
                          ))}
                        </div>
                      ) : (
                        <p className="helper">No matches found via reverse image search.</p>
                      )}
                    </div>
                  ) : (
                    <div style={{ marginTop: '1rem' }}>
                      <div className="score-pill score-neutral">
                        <span className="score-label">Source Verification</span>
                        <span className="score-value-text">Not assessed</span>
                        <span>{isAddonEnabled('reverse_search') ? 'Module not selected by triage agent' : 'Add-on module disabled'}</span>
                      </div>
                    </div>
                  )}
                </section>

                {/* Card 7: Provenance — always shown */}
                <section className="card">
                  <h2>Provenance</h2>
                  <p className="helper">
                    Blockchain-style immutable audit trail tracking image history and observation chain.
                  </p>
                  {provenanceData ? (
                    <div style={{ marginTop: '1rem' }}>
                      <div className="provenance-meta">
                        <p><strong>Chain ID:</strong> <code>{provenanceData.chain_id}</code></p>
                        <p><strong>Status:</strong> <span className="pill pill-success">{provenanceData.status}</span></p>
                        <p><strong>Blocks:</strong> {provenanceData.blocks?.length || 0}</p>
                        {provenanceData.blockchain_tx_hash && (
                          <p>
                            <strong>Blockchain anchor:</strong>{' '}
                            <code>{provenanceData.blockchain_tx_hash.substring(0, 18)}…</code>
                            {provenanceData.blockchain_verification_url &&
                            !provenanceData.blockchain_verification_url.startsWith('local://') && (
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
                            )}
                          </p>
                        )}
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
                              {block.observation_data && (
                                <details>
                                  <summary>View observation data</summary>
                                  <pre className="code-block">{JSON.stringify(block.observation_data, null, 2)}</pre>
                                </details>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="helper">No provenance blocks available.</p>
                      )}
                    </div>
                  ) : (
                    <div style={{ marginTop: '1rem' }}>
                      <div className="score-pill score-neutral">
                        <span className="score-label">Provenance</span>
                        <span className="score-value-text">Not assessed</span>
                        <span>{isAddonEnabled('provenance') ? 'Module not selected by triage agent' : 'Add-on module disabled'}</span>
                      </div>
                    </div>
                  )}
                </section>

              </div>
            )}

          </>
        )}
      </main>
      {/* Run confirmation modal */}
      {showRunModal && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="run-modal-title"
          style={{
            position: 'fixed', inset: 0, zIndex: 1000,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: 'rgba(0,0,0,0.55)',
            padding: '1rem',
          }}
          onClick={(e) => { if (e.target === e.currentTarget) setShowRunModal(false) }}
        >
          <div style={{
            background: 'var(--surface, #fff)',
            borderRadius: '14px',
            padding: '2rem',
            maxWidth: '520px',
            width: '100%',
            boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
          }}>
            <h2 id="run-modal-title" style={{ margin: '0 0 0.5rem 0', fontSize: '1.25rem' }}>
              Ready to run analysis?
            </h2>

            {/* Provider-aware patience message */}
            {providerStatus?.active_provider === 'llama_cpp' ? (
              <div style={{
                margin: '1rem 0',
                padding: '0.875rem 1rem',
                background: 'rgba(245,158,11,0.1)',
                border: '1px solid rgba(245,158,11,0.4)',
                borderRadius: '8px',
              }}>
                <div style={{ fontWeight: '700', color: '#92400e', marginBottom: '0.25rem' }}>
                  ⏳ Local CPU inference — please be patient
                </div>
                <div style={{ fontSize: '0.88rem', color: '#78350f', lineHeight: 1.5 }}>
                  Analysis runs locally on the server CPU. This is completely free and
                  private, but takes <strong>2–3 minutes</strong> per request. Do not
                  close or reload this page while the analysis is running.
                </div>
              </div>
            ) : providerStatus?.active_provider === 'byo_gpu' ? (
              <div style={{
                margin: '1rem 0',
                padding: '0.875rem 1rem',
                background: 'rgba(59,130,246,0.08)',
                border: '1px solid rgba(59,130,246,0.3)',
                borderRadius: '8px',
              }}>
                <div style={{ fontWeight: '700', color: '#1d4ed8', marginBottom: '0.25rem' }}>
                  🖥️ BYO GPU endpoint active
                </div>
                <div style={{ fontSize: '0.88rem', color: '#1e3a5f', lineHeight: 1.5 }}>
                  Analysis will run on your configured GPU server. Typical response
                  time is under 30 seconds.
                </div>
              </div>
            ) : (
              <div style={{
                margin: '1rem 0',
                padding: '0.875rem 1rem',
                background: 'rgba(16,185,129,0.07)',
                border: '1px solid rgba(16,185,129,0.3)',
                borderRadius: '8px',
              }}>
                <div style={{ fontWeight: '700', color: '#065f46', marginBottom: '0.25rem' }}>
                  ☁️ Cloud inference
                </div>
                <div style={{ fontSize: '0.88rem', color: '#064e3b', lineHeight: 1.5 }}>
                  Analysis will run via a cloud AI provider. Typical response time is
                  5–30 seconds.
                </div>
              </div>
            )}

            {/* What will happen */}
            <div style={{ fontSize: '0.88rem', color: 'var(--ink-soft, #4b5563)', lineHeight: 1.6, marginBottom: '1.25rem' }}>
              <strong style={{ display: 'block', marginBottom: '0.4rem', color: 'var(--ink, #111)' }}>
                What the analysis covers:
              </strong>
              <ul style={{ margin: '0', paddingLeft: '1.25rem' }}>
                <li><strong>Claim Veracity</strong> — Is the accompanying claim medically accurate?</li>
                <li><strong>Image-Context Alignment</strong> — Does this image actually support the claim?</li>
                {forceTools.size > 0 && (
                  <li><strong>Add-on modules</strong> — {Array.from(forceTools).join(', ')}</li>
                )}
              </ul>
            </div>

            {/* Fair-use rules */}
            <div style={{
              fontSize: '0.82rem',
              color: 'var(--muted, #6b7280)',
              background: 'rgba(0,0,0,0.03)',
              borderRadius: '6px',
              padding: '0.75rem 1rem',
              marginBottom: '1.5rem',
              lineHeight: 1.55,
            }}>
              <strong style={{ color: 'var(--ink-soft, #374151)' }}>Fair-use policy</strong>
              {providerStatus?.active_provider === 'llama_cpp' ? (
                <> · Local inference is limited to <strong>5 requests per hour</strong> per
                user to ensure fair access for everyone. Each request occupies the model for
                2–3 minutes, so please only submit when you are ready.</>
              ) : (
                <> · Cloud requests are limited to <strong>10 requests per hour</strong> per
                user to prevent abuse.</>
              )} Repeated rapid submissions will be automatically rate-limited.
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button
                type="button"
                onClick={() => setShowRunModal(false)}
                style={{
                  padding: '0.625rem 1.25rem',
                  background: 'transparent',
                  border: '1px solid var(--border, #d1d5db)',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: '600',
                  color: 'var(--ink-soft, #374151)',
                  fontSize: '0.9rem',
                }}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmRun}
                style={{
                  padding: '0.625rem 1.5rem',
                  background: '#5b8def',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: '700',
                  color: '#fff',
                  fontSize: '0.9rem',
                }}
              >
                Run analysis
              </button>
            </div>
          </div>
        </div>
      )}

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
