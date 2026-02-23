import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react'

// Inject @keyframes once so inline animation properties work
const KEYFRAMES_ID = 'llama-status-keyframes'
if (typeof document !== 'undefined' && !document.getElementById(KEYFRAMES_ID)) {
  const style = document.createElement('style')
  style.id = KEYFRAMES_ID
  style.textContent = `
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.6; }
    }
    @keyframes pulse-dot {
      0%, 100% { transform: scale(1); opacity: 1; }
      50% { transform: scale(1.4); opacity: 0.5; }
    }
  `
  document.head.appendChild(style)
}

/**
 * LlamaCppStatus — polls the /api/v1/config/provider-status endpoint every
 * 5 seconds and surfaces the current provider state to the rest of the app.
 *
 * Props:
 *   apiBase        — base URL for the API
 *   accessCode     — optional demo access code header
 *   onStatusChange — callback(status) called whenever the status changes
 *                    status shape: { active_provider, busy, busy_since_secs,
 *                                    byo_gpu_configured, auto_revert_in_secs }
 *
 * Renders a compact inline status chip that can appear in multiple places.
 */
const LlamaCppStatus = forwardRef(function LlamaCppStatus(
  { apiBase = '', accessCode = '', onStatusChange },
  ref,
) {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(false)
  const intervalRef = useRef(null)
  const onStatusChangeRef = useRef(onStatusChange)

  useEffect(() => {
    onStatusChangeRef.current = onStatusChange
  }, [onStatusChange])

  const fetchStatus = useCallback(async () => {
    try {
      const headers = {}
      if (accessCode) headers['X-Demo-Access-Code'] = accessCode
      const base = apiBase.replace(/\/$/, '')
      const res = await fetch(`${base}/api/v1/config/provider-status`, { headers })
      if (!res.ok) {
        setError(true)
        return
      }
      const data = await res.json()
      setError(false)
      setStatus(data)
      if (onStatusChangeRef.current) onStatusChangeRef.current(data)
    } catch {
      setError(true)
    }
  }, [apiBase, accessCode])

  // Expose refresh() so parent can trigger an immediate poll
  useImperativeHandle(ref, () => ({ refresh: fetchStatus }), [fetchStatus])

  // Initial fetch on mount and when API params change — does NOT depend on status
  useEffect(() => {
    fetchStatus()
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [apiBase, accessCode, fetchStatus])

  // Polling interval setup — depends only on fetchStatus and status?.busy
  useEffect(() => {
    const interval = status?.busy ? 2000 : 5000
    intervalRef.current = setInterval(fetchStatus, interval)
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [fetchStatus, status?.busy])

  if (error || !status) return null

  return <StatusChip status={status} />
})

/**
 * StatusChip — the visual component.  Can be used standalone anywhere.
 */
export function StatusChip({ status }) {
  if (!status) return null

  const { active_provider, busy, busy_since_secs, byo_gpu_configured, auto_revert_in_secs } = status

  // ── BYO GPU active ──
  if (active_provider === 'byo_gpu') {
    const revertLabel = auto_revert_in_secs != null
      ? ` · reverts in ${Math.ceil(auto_revert_in_secs)}s`
      : ''
    return (
      <div style={chipStyle('#3b82f6', 'rgba(59,130,246,0.1)')}>
        <span style={dotStyle('#3b82f6')} />
        <span>BYO GPU Active{revertLabel}</span>
      </div>
    )
  }

  // ── llama-cpp busy ──
  if (active_provider === 'llama_cpp' && busy) {
    const sinceLabel = busy_since_secs != null ? ` · ${Math.round(busy_since_secs)}s` : ''
    return (
      <div style={{ ...chipStyle('#f59e0b', 'rgba(245,158,11,0.1)'), animation: 'pulse 1.5s infinite' }}>
        <span style={{ ...dotStyle('#f59e0b'), animation: 'pulse-dot 1.5s infinite' }} />
        <span>Local AI Processing{sinceLabel} — please wait 2–3 min</span>
      </div>
    )
  }

  // ── llama-cpp idle ──
  if (active_provider === 'llama_cpp') {
    return (
      <div style={chipStyle('#10b981', 'rgba(16,185,129,0.08)')}>
        <span style={dotStyle('#10b981')} />
        <span>Local AI Ready</span>
      </div>
    )
  }

  // ── cloud provider (HuggingFace / Vertex) ──
  return (
    <div style={chipStyle('#6b7280', 'rgba(107,114,128,0.08)')}>
      <span style={dotStyle('#6b7280')} />
      <span>Cloud Provider</span>
    </div>
  )
}

function chipStyle(color, bg) {
  return {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.4rem',
    padding: '0.3rem 0.75rem',
    background: bg,
    border: `1px solid ${color}44`,
    borderRadius: '999px',
    fontSize: '0.8rem',
    fontWeight: '600',
    color,
    whiteSpace: 'nowrap',
  }
}

function dotStyle(color) {
  return {
    width: '7px',
    height: '7px',
    borderRadius: '50%',
    background: color,
    flexShrink: 0,
  }
}

export default LlamaCppStatus
