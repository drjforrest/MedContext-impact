import { useEffect, useRef, useState } from 'react'
import './SettingsAndTools.css'
import { StatusChip } from './components/LlamaCppStatus'

function SettingsAndTools({
  apiBase,
  accessCode,
  onApiBaseChange,
  onAccessCodeChange,
  defaultApiBase,
  availableModels,
  selectedModel,
  onModelSelect,
  onConfigSave
}) {
  // Provider configuration state
  const [providerType, setProviderType] = useState('llama_cpp')
  const [hfToken, setHfToken] = useState('')
  const [vertexProject, setVertexProject] = useState('')
  const [vertexEndpoint, setVertexEndpoint] = useState('')
  const [vertexApiKey, setVertexApiKey] = useState('')

  // LLM configuration state
  const [llmProvider, setLlmProvider] = useState('gemini')
  const [geminiApiKey, setGeminiApiKey] = useState('')
  const [openrouterApiKey, setOpenrouterApiKey] = useState('')

  // Status state
  const [testStatus, setTestStatus] = useState('')
  const [providerInfo, setProviderInfo] = useState(null)

  // BYO GPU state
  const [byoGpuEndpoint, setByoGpuEndpoint] = useState('')
  const [byoGpuApiKey, setByoGpuApiKey] = useState('')
  const [byoGpuStatus, setByoGpuStatus] = useState('')

  // Live provider status (polled every 5s while this component is mounted)
  const [liveStatus, setLiveStatus] = useState(null)
  const pollRef = useRef(null)

  // Load saved configuration from sessionStorage (secrets never persist across sessions)
  useEffect(() => {
    const savedConfig = sessionStorage.getItem('medcontext_provider_config')
    if (savedConfig) {
      try {
        const config = JSON.parse(savedConfig)
        setProviderType(config.providerType || 'llama_cpp')
        setHfToken(config.hfToken || '')
        setVertexProject(config.vertexProject || '')
        setVertexEndpoint(config.vertexEndpoint || '')
        setVertexApiKey(config.vertexApiKey || '')
        setLlmProvider(config.llmProvider || 'gemini')
        setGeminiApiKey(config.geminiApiKey || '')
        setOpenrouterApiKey(config.openrouterApiKey || '')
      } catch {
        // Ignore invalid sessionStorage data — defaults will be used
      }
    }
    // Migrate: clear any secrets previously stored in localStorage
    localStorage.removeItem('medcontext_provider_config')
  }, [])

  // Sync providerInfo from availableModels
  useEffect(() => {
    if (availableModels && availableModels.length > 0) {
      const currentProvider = availableModels.find(m => m.model === selectedModel)
      setProviderInfo(currentProvider)
    }
  }, [availableModels, selectedModel])

  // Poll /api/v1/config/provider-status every 5s while the settings page is open
  useEffect(() => {
    const fetchLiveStatus = async () => {
      try {
        const headers = {}
        if (accessCode) headers['X-Demo-Access-Code'] = accessCode
        const base = (apiBase || defaultApiBase || '').replace(/\/$/, '')
        const res = await fetch(`${base}/api/v1/config/provider-status`, { headers })
        if (res.ok) {
          setLiveStatus(await res.json())
        }
      } catch {
        // Backend may not be running locally — silent
      }
    }

    fetchLiveStatus()
    pollRef.current = setInterval(fetchLiveStatus, 5000)
    return () => clearInterval(pollRef.current)
  }, [apiBase, accessCode, defaultApiBase])

  const handleActivateBYOGPU = async () => {
    if (!byoGpuEndpoint.trim()) {
      setByoGpuStatus('error:Please enter an endpoint URL.')
      return
    }
    setByoGpuStatus('pending:Activating BYO GPU...')
    try {
      const headers = { 'Content-Type': 'application/json' }
      if (accessCode) headers['X-Demo-Access-Code'] = accessCode
      const base = (apiBase || defaultApiBase || '').replace(/\/$/, '')
      const res = await fetch(`${base}/api/v1/config/activate-byo-gpu`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ endpoint: byoGpuEndpoint.trim(), api_key: byoGpuApiKey.trim() }),
      })
      const data = await res.json()
      if (res.ok) {
        setByoGpuStatus(`success:${data.message}`)
      } else {
        setByoGpuStatus(`error:${data.detail || 'Failed to activate BYO GPU.'}`)
      }
    } catch (err) {
      setByoGpuStatus(`error:${err.message}`)
    }
  }

  const handleRevertToLocal = async () => {
    setByoGpuStatus('pending:Reverting to local llama-cpp...')
    try {
      const headers = { 'Content-Type': 'application/json' }
      if (accessCode) headers['X-Demo-Access-Code'] = accessCode
      const base = (apiBase || defaultApiBase || '').replace(/\/$/, '')
      const res = await fetch(`${base}/api/v1/config/revert-to-local`, {
        method: 'POST',
        headers,
      })
      const data = await res.json()
      if (res.ok) {
        setByoGpuStatus(`success:${data.message}`)
      } else {
        setByoGpuStatus(`error:${data.detail || 'Failed to revert.'}`)
      }
    } catch (err) {
      setByoGpuStatus(`error:${err.message}`)
    }
  }

  const handleSaveConfiguration = () => {
    const hasSecrets = [hfToken, vertexApiKey, geminiApiKey, openrouterApiKey].some(k => k.trim())
    if (hasSecrets) {
      const proceed = window.confirm(
        'API keys will be stored in your browser session memory. ' +
        'They are cleared when you close this tab. ' +
        'For production use, configure keys in the server .env file instead.\n\nContinue?'
      )
      if (!proceed) return
    }
    const config = {
      providerType, hfToken, vertexProject, vertexEndpoint, vertexApiKey,
      llmProvider, geminiApiKey, openrouterApiKey,
    }
    sessionStorage.setItem('medcontext_provider_config', JSON.stringify(config))
    if (onConfigSave) onConfigSave(config)
    setTestStatus('success:Configuration saved to session. Keys are cleared when you close this tab.')
  }

  const handleTestConnection = async () => {
    setTestStatus('pending:Testing connection...')
    try {
      const base = (apiBase || defaultApiBase || '').replace(/\/$/, '')
      const url = `${base}/api/v1/orchestrator/providers`
      const headers = {}
      if (accessCode) headers['X-Demo-Access-Code'] = accessCode
      const res = await fetch(url, { headers })
      if (res.ok) {
        const providers = await res.json()
        const count = providers.filter(p => p.available).length
        setTestStatus(`success:Connected! ${count} provider(s) available.`)
      } else {
        setTestStatus('error:Connection failed. Check your configuration.')
      }
    } catch (err) {
      setTestStatus(`error:${err.message}`)
    }
  }

  // Helper to parse the "state:message" status strings
  const parseStatus = (s) => {
    if (!s) return null
    const colon = s.indexOf(':')
    if (colon === -1) return { state: s, msg: '' }
    return { state: s.slice(0, colon), msg: s.slice(colon + 1) }
  }

  return (
    <div className="settings-and-tools">
      <div className="settings-tools-header">
        <h1>Settings &amp; Tools</h1>
        <p className="st-helper">Configure providers, model, and API settings</p>
      </div>

      {/* ── Live Runtime Status ─────────────────────────────────────── */}
      {liveStatus && (
        <section className="st-card st-status-card">
          <div className="st-status-row">
            <div>
              <div className="st-label">Active Provider Status</div>
              <StatusChip status={liveStatus} />
            </div>
            {liveStatus.active_provider === 'byo_gpu' && liveStatus.auto_revert_in_secs != null && (
              <div className="st-status-aside">
                Auto-reverts to llama-cpp in<br />
                <strong>{Math.ceil(liveStatus.auto_revert_in_secs)}s</strong>
              </div>
            )}
            {liveStatus.active_provider === 'llama_cpp' && liveStatus.busy && (
              <div className="st-status-aside st-warn">
                Processing a request — please wait 2–3 min
              </div>
            )}
          </div>
        </section>
      )}

      {/* ── MedGemma Provider ─────────────────────────────────────── */}
      <section className="st-card">
        <h2>MedGemma Provider</h2>
        <p className="st-helper">Configure the medical image analysis engine</p>

        {providerInfo && (
          <div className={`st-notice ${providerInfo.available ? 'st-notice--success' : 'st-notice--error'}`}>
            <div className="st-notice-row">
              <div>
                <strong>{providerInfo.name}</strong>
                <span className="st-helper" style={{ marginLeft: '0.5rem' }}>{providerInfo.description}</span>
              </div>
              <span className={`st-badge ${providerInfo.available ? 'st-badge--green' : 'st-badge--red'}`}>
                {providerInfo.available ? '● Available' : '● Unavailable'}
              </span>
            </div>
          </div>
        )}

        {/* Comparison cards */}
        <div className="st-compare-grid">
          <div className="st-compare-card st-compare-card--green">
            <h4>🖥️ Local GGUF</h4>
            <ul>
              <li>✅ Free — no API costs</li>
              <li>✅ Privacy-preserving</li>
              <li>✅ Works offline</li>
              <li>⚠️ Requires ~4 GB RAM</li>
            </ul>
          </div>
          <div className="st-compare-card st-compare-card--blue">
            <h4>🤗 HuggingFace</h4>
            <ul>
              <li>✅ No server resources</li>
              <li>✅ Free tier available</li>
              <li>⚠️ 5–10 s cold-start latency</li>
              <li>⚠️ Requires API token</li>
            </ul>
          </div>
          <div className="st-compare-card st-compare-card--red">
            <h4>☁️ Vertex AI</h4>
            <ul>
              <li>✅ &lt;1 s latency</li>
              <li>✅ Auto-scaling</li>
              <li>⚠️ Requires GCP account</li>
              <li>⚠️ Usage costs</li>
            </ul>
          </div>
        </div>

        {/* Provider radio buttons */}
        <div className="st-section">
          <h3>Select Provider</h3>

          <div className="st-radio-group">
            <label className="st-radio-label">
              <input
                type="radio" name="provider" value="llama_cpp"
                checked={providerType === 'llama_cpp'}
                onChange={(e) => setProviderType(e.target.value)}
              />
              <strong>Local GGUF (Default)</strong>
            </label>
            {providerType === 'llama_cpp' && (
              <div className="st-radio-detail">
                <p className="st-helper">
                  ✅ Already configured on the server. No additional setup required.<br />
                  Model: <code>/var/www/medcontext/models/medgemma-1.5-4b-it-Q4_K_M.gguf</code>
                </p>
              </div>
            )}
          </div>

          <div className="st-radio-group">
            <label className="st-radio-label">
              <input
                type="radio" name="provider" value="huggingface"
                checked={providerType === 'huggingface'}
                onChange={(e) => setProviderType(e.target.value)}
              />
              <strong>HuggingFace Inference API</strong>
            </label>
            {providerType === 'huggingface' && (
              <div className="st-radio-detail">
                <label className="field">
                  <span>HuggingFace Token</span>
                  <input
                    type="password"
                    placeholder="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    value={hfToken}
                    onChange={(e) => setHfToken(e.target.value)}
                  />
                  <span className="helper">
                    Get your token at huggingface.co/settings/tokens
                  </span>
                </label>
              </div>
            )}
          </div>

          <div className="st-radio-group">
            <label className="st-radio-label">
              <input
                type="radio" name="provider" value="vertex"
                checked={providerType === 'vertex'}
                onChange={(e) => setProviderType(e.target.value)}
              />
              <strong>Google Vertex AI</strong>
            </label>
            {providerType === 'vertex' && (
              <div className="st-radio-detail st-grid">
                <label className="field">
                  <span>GCP Project ID</span>
                  <input type="text" placeholder="your-gcp-project-id"
                    value={vertexProject} onChange={(e) => setVertexProject(e.target.value)} />
                </label>
                <label className="field">
                  <span>Vertex AI Endpoint URL</span>
                  <input type="url" placeholder="https://us-central1-aiplatform.googleapis.com/v1/..."
                    value={vertexEndpoint} onChange={(e) => setVertexEndpoint(e.target.value)} />
                </label>
                <label className="field">
                  <span>Vertex API Key</span>
                  <input type="password" placeholder="Your Vertex AI API key"
                    value={vertexApiKey} onChange={(e) => setVertexApiKey(e.target.value)} />
                </label>
                <p className="helper">
                  You must deploy MedGemma to Vertex AI first. See Vertex AI documentation.
                </p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* ── BYO GPU Endpoint ──────────────────────────────────────── */}
      <section className="st-card st-card--indigo">
        <h2>BYO GPU Endpoint <span className="st-tag">Production · Admin only</span></h2>
        <p className="st-helper">
          Have your own GPU server running MedGemma via an OpenAI-compatible API?
          Activate it here. The server automatically reverts to local llama-cpp after
          <strong> 2 minutes of inactivity</strong>.
        </p>

        {liveStatus?.active_provider === 'byo_gpu' ? (
          <div>
            <div className="st-notice st-notice--info">
              <strong>BYO GPU is currently active.</strong>
              {liveStatus.auto_revert_in_secs != null && (
                <span className="st-muted"> Auto-reverts in {Math.ceil(liveStatus.auto_revert_in_secs)}s</span>
              )}
              {liveStatus.byo_gpu_endpoint_hint && (
                <div className="st-mono">{liveStatus.byo_gpu_endpoint_hint}</div>
              )}
            </div>
            <button type="button" className="st-btn st-btn--ghost" onClick={handleRevertToLocal}>
              Revert to Local llama-cpp
            </button>
          </div>
        ) : (
          <div className="st-grid">
            <label className="field">
              <span>GPU Endpoint URL</span>
              <input type="url" placeholder="https://your-gpu-server:8000"
                value={byoGpuEndpoint} onChange={(e) => setByoGpuEndpoint(e.target.value)} />
              <span className="helper">OpenAI-compatible base URL</span>
            </label>
            <label className="field">
              <span>API Key <span className="st-optional">(optional)</span></span>
              <input type="password" placeholder="Bearer token or API key"
                value={byoGpuApiKey} onChange={(e) => setByoGpuApiKey(e.target.value)} />
            </label>
            <div>
              <button type="button" className="st-btn st-btn--indigo" onClick={handleActivateBYOGPU}>
                Activate BYO GPU
              </button>
              <span className="st-helper" style={{ marginLeft: '0.75rem' }}>Requires admin IP access</span>
            </div>
          </div>
        )}

        {byoGpuStatus && (() => {
          const { state, msg } = parseStatus(byoGpuStatus)
          return (
            <div className={`st-notice st-notice--${state === 'success' ? 'success' : state === 'pending' ? 'warn' : 'error'}`}
              style={{ marginTop: '0.75rem' }}>
              {msg}
            </div>
          )
        })()}
      </section>

      {/* ── LLM Orchestrator ─────────────────────────────────────── */}
      <section className="st-card">
        <h2>LLM Orchestrator</h2>
        <p className="st-helper">
          Handles contextual reasoning and alignment analysis. Required for the full pipeline.
        </p>

        <div className="st-section">
          <div className="st-radio-group">
            <label className="st-radio-label">
              <input
                type="radio" name="llm_provider" value="gemini"
                checked={llmProvider === 'gemini'}
                onChange={(e) => setLlmProvider(e.target.value)}
              />
              <strong>Google Gemini</strong>
              <span className="st-recommended">Recommended — 1 500 free requests/day</span>
            </label>
            {llmProvider === 'gemini' && (
              <div className="st-radio-detail">
                <label className="field">
                  <span>Gemini API Key</span>
                  <input type="password" placeholder="Your Gemini API key"
                    value={geminiApiKey} onChange={(e) => setGeminiApiKey(e.target.value)} />
                  <span className="helper">Get your key at aistudio.google.com/app/apikey</span>
                </label>
              </div>
            )}
          </div>

          <div className="st-radio-group">
            <label className="st-radio-label">
              <input
                type="radio" name="llm_provider" value="openrouter"
                checked={llmProvider === 'openrouter'}
                onChange={(e) => setLlmProvider(e.target.value)}
              />
              <strong>OpenRouter</strong>
              <span className="st-muted" style={{ marginLeft: '0.5rem' }}>Multi-provider</span>
            </label>
            {llmProvider === 'openrouter' && (
              <div className="st-radio-detail">
                <label className="field">
                  <span>OpenRouter API Key</span>
                  <input type="password" placeholder="sk-or-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    value={openrouterApiKey} onChange={(e) => setOpenrouterApiKey(e.target.value)} />
                  <span className="helper">Get your key at openrouter.ai/keys</span>
                </label>
              </div>
            )}
          </div>
        </div>

        {/* Save / Test actions */}
        <div className="st-actions">
          <button type="button" className="st-btn st-btn--primary" onClick={handleSaveConfiguration}>
            Save Configuration
          </button>
          <button type="button" className="st-btn st-btn--ghost" onClick={handleTestConnection}>
            Test Connection
          </button>
        </div>

        {testStatus && (() => {
          const { state, msg } = parseStatus(testStatus)
          return (
            <div className={`st-notice st-notice--${state === 'success' ? 'success' : state === 'pending' ? 'warn' : 'error'}`}>
              {msg}
            </div>
          )
        })()}

        <div className="st-notice st-notice--info" style={{ marginTop: '1.5rem' }}>
          <strong>Note:</strong> Configuration is saved to your browser session only and is cleared when you close the tab.
          For persistent configuration, update the <code>.env</code> file on the server and restart the service.
        </div>
      </section>

      {/* ── Model Selection ──────────────────────────────────────── */}
      <section className="st-card">
        <h2>Model Selection</h2>
        <p className="st-helper">Choose which MedGemma model to use for analysis</p>

        {availableModels && availableModels.length > 0 ? (
          <div className="st-section">
            <div className="st-model-list">
              {availableModels.map((m) => (
                <label
                  key={m.id}
                  className={`st-model-item ${selectedModel === m.model ? 'st-model-item--active' : ''} ${!m.available ? 'st-model-item--disabled' : ''}`}
                >
                  <input
                    type="radio" name="medgemma_model" value={m.model}
                    checked={selectedModel === m.model}
                    disabled={!m.available}
                    onChange={(e) => onModelSelect?.(e.target.value)}
                  />
                  <div className="st-model-info">
                    <div className="st-model-name-row">
                      <strong>{m.name}</strong>
                      <span className={`st-badge ${m.available ? 'st-badge--green' : 'st-badge--red'}`}>
                        {m.available ? 'Available' : 'Unavailable'}
                      </span>
                    </div>
                    <p className="st-helper">{m.description}</p>
                    <div className="st-model-meta">
                      <span>Provider: <code>{m.provider}</code></span>
                      <span>Model: <code>{m.model}</code></span>
                      <span>
                        Thresholds: V={m.recommended_veracity_threshold} / A={m.recommended_alignment_threshold}
                        · Logic: {m.recommended_decision_logic}
                      </span>
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        ) : (
          <div className="st-empty">No models available. Check your provider configuration.</div>
        )}
      </section>

      {/* ── API Settings ─────────────────────────────────────────── */}
      <section className="st-card">
        <h2>API Settings</h2>
        <p className="st-helper">Configure API endpoints and access codes</p>

        <div className="st-section st-grid">
          <label className="field">
            <span>API base URL</span>
            <input
              type="url"
              placeholder={defaultApiBase}
              value={apiBase}
              onChange={(e) => onApiBaseChange(e.target.value)}
            />
            <span className="helper">
              Stored locally in your browser. Default: {defaultApiBase || 'http://localhost:8000'}
            </span>
          </label>
          <label className="field">
            <span>Demo Access Code</span>
            <input
              type="text"
              placeholder="Leave empty for local dev"
              value={accessCode}
              onChange={(e) => onAccessCodeChange(e.target.value)}
            />
            <span className="helper">Required for public demo. Leave empty for local development.</span>
          </label>
        </div>
      </section>

      {/* ── About ────────────────────────────────────────────────── */}
      <section className="st-card about-card">
        <div className="about-content">
          <h2>About MedContext</h2>

          <div className="about-section">
            <h3>The Problem</h3>
            <p>
              Medical misinformation doesn&apos;t require fake images. The dominant real-world threat uses
              <strong> authentic medical scans</strong> paired with <strong>false or misleading claims</strong>.
              Current solutions focus on pixel forensics, missing the contextual deception that represents
              the majority of medical misinformation.
            </p>
          </div>

          <div className="about-section">
            <h3>The Solution</h3>
            <p>MedContext evaluates <strong>contextual authenticity</strong> through two signals:</p>
            <ul>
              <li><strong>Claim Veracity</strong> — Is the accompanying claim medically accurate?</li>
              <li><strong>Image-Claim Alignment</strong> — Does the image actually support the claim?</li>
            </ul>
            <p>
              Individual signals are insufficient (veracity 79.8%, alignment 86.5%). But <strong>hierarchical
              optimization</strong> with smart thresholds (0.65/0.30) and VERACITY_FIRST logic achieves
              <strong> 92.0% accuracy</strong> on the Med-MMHL benchmark.
            </p>
          </div>

          <div className="about-section">
            <h3>Validation</h3>
            <p>
              Validated on <strong>Med-MMHL</strong> — a research-grade dataset of real-world fact-checked
              medical misinformation samples from LeadStories, FactCheck.org, Snopes, and health authorities.
            </p>
            <div className="stats-grid">
              <div className="stat-box"><span className="stat-number">92.0%</span><span className="stat-label">Accuracy</span></div>
              <div className="stat-box"><span className="stat-number">96.2%</span><span className="stat-label">Precision</span></div>
              <div className="stat-box"><span className="stat-number">94.1%</span><span className="stat-label">Recall</span></div>
              <div className="stat-box"><span className="stat-number">95.1%</span><span className="stat-label">F1 Score</span></div>
            </div>
            <p className="helper" style={{ marginTop: '1rem' }}>
              n=163 stratified random sample (seed=42), MedGemma 4B Q4_KM quantized model
            </p>
          </div>

          <div className="about-section">
            <h3>Technical Architecture</h3>
            <ul>
              <li><strong>MedGemma 4B</strong> — Google&apos;s medical multimodal model</li>
              <li><strong>LangGraph Agent</strong> — Orchestrated analysis workflow</li>
              <li><strong>Hierarchical Decision Logic</strong> — VERACITY_FIRST with optimized thresholds</li>
              <li><strong>Efficient Deployment</strong> — Quantized 4-bit model via llama-cpp-python</li>
            </ul>
          </div>

          <div className="about-section">
            <h3>Impact &amp; Deployment</h3>
            <p>
              Partnership with <strong>HERO Lab, University of British Columbia</strong> for deployment
              to African Ministries of Health and rural clinical settings. Target scale: millions of
              patients via Telegram bot integration.
            </p>
          </div>

          <div className="about-section about-footer">
            <h3>Project Information</h3>
            <div className="info-grid">
              <div><strong>Developer</strong><p>Jamie Forrest</p></div>
              <div>
                <strong>Affiliation</strong>
                <p>HERO Lab, School of Nursing<br />University of British Columbia</p>
              </div>
              <div>
                <strong>Contact</strong>
                <p>
                  <a href="mailto:james.forrest@ubc.ca">james.forrest@ubc.ca</a><br />
                  <a href="mailto:forrest.jamie@gmail.com">forrest.jamie@gmail.com</a>
                </p>
              </div>
              <div>
                <strong>Repository</strong>
                <p>
                  <a href="https://github.com/drjforrest/medcontext" target="_blank" rel="noopener noreferrer">
                    github.com/drjforrest/medcontext
                  </a>
                </p>
              </div>
            </div>
            <p className="helper" style={{ marginTop: '1.5rem', textAlign: 'center' }}>
              February 2026 · MedGemma 4B Q4_KM · Med-MMHL (n=163)
            </p>
          </div>
        </div>
      </section>
    </div>
  )
}

export default SettingsAndTools
