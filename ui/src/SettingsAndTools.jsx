import { useState } from 'react'
import ThresholdOptimization from './ThresholdOptimization'
import './SettingsAndTools.css'

function SettingsAndTools({ apiBase, accessCode, onApiBaseChange, onAccessCodeChange, defaultApiBase }) {
  const [activeTab, setActiveTab] = useState('tools')

  return (
    <div className="settings-and-tools">
      <div className="settings-tools-header">
        <h1>Settings & Tools</h1>
        <p className="helper">
          Threshold optimization tool, API configuration, and project information
        </p>
      </div>

      <nav className="sub-tab-bar">
        <button
          type="button"
          className={`sub-tab-button ${activeTab === 'tools' ? 'sub-tab-active' : ''}`}
          onClick={() => setActiveTab('tools')}
        >
          Threshold Optimization
        </button>
        <button
          type="button"
          className={`sub-tab-button ${activeTab === 'settings' ? 'sub-tab-active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          Settings
        </button>
        <button
          type="button"
          className={`sub-tab-button ${activeTab === 'about' ? 'sub-tab-active' : ''}`}
          onClick={() => setActiveTab('about')}
        >
          About
        </button>
      </nav>

      <div className="sub-tab-content">
        {activeTab === 'tools' ? (
          <ThresholdOptimization apiBase={apiBase} accessCode={accessCode} />
        ) : activeTab === 'settings' ? (
          <section className="card settings-card">
            <div className="settings-header">
              <div>
                <h2>API Configuration</h2>
                <p className="helper">
                  Configure API endpoints and access codes
                </p>
              </div>
            </div>
            <div className="settings-section">
              <h3>API Settings</h3>
              <div className="grid">
                <label className="field">
                  <span>API base URL</span>
                  <input
                    type="url"
                    placeholder={defaultApiBase}
                    value={apiBase}
                    onChange={(event) => onApiBaseChange(event.target.value)}
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
                    onChange={(event) => onAccessCodeChange(event.target.value)}
                  />
                  <span className="helper">
                    Required for public demo. Leave empty for local development.
                  </span>
                </label>
              </div>
            </div>
          </section>
        ) : (
          <section className="card about-card">
            <div className="about-content">
              <h2>About MedContext</h2>

              <div className="about-section">
                <h3>The Problem</h3>
                <p>
                  Medical misinformation doesn't require fake images. The dominant real-world threat uses
                  <strong> authentic medical scans</strong> (X-rays, CT, clinical photos) paired with
                  <strong> false or misleading claims</strong>. Current solutions focus on pixel forensics,
                  missing the contextual deception that represents the majority of medical misinformation.
                </p>
              </div>

              <div className="about-section">
                <h3>The Solution</h3>
                <p>
                  MedContext evaluates <strong>contextual authenticity</strong> through two signals:
                </p>
                <ul>
                  <li><strong>Claim Veracity</strong> — Is the accompanying claim medically accurate?</li>
                  <li><strong>Image-Claim Alignment</strong> — Does the image actually support the claim?</li>
                </ul>
                <p>
                  Individual signals are insufficient (veracity 79.8%, alignment 86.5%). But <strong>hierarchical
                  optimization</strong> with smart thresholds (0.65/0.30) and VERACITY_FIRST logic achieves
                  breakthrough performance: <strong>92.0% accuracy</strong> on the Med-MMHL benchmark.
                </p>
              </div>

              <div className="about-section">
                <h3>Validation</h3>
                <p>
                  Validated on <strong>Med-MMHL</strong> (Medical Multimodal Misinformation Benchmark) — a
                  research-grade dataset of 1,785 real-world fact-checked medical misinformation samples from
                  LeadStories, FactCheck.org, Snopes, and health authorities.
                </p>
                <div className="stats-grid">
                  <div className="stat-box">
                    <span className="stat-number">92.0%</span>
                    <span className="stat-label">Accuracy</span>
                  </div>
                  <div className="stat-box">
                    <span className="stat-number">96.2%</span>
                    <span className="stat-label">Precision</span>
                  </div>
                  <div className="stat-box">
                    <span className="stat-number">94.1%</span>
                    <span className="stat-label">Recall</span>
                  </div>
                  <div className="stat-box">
                    <span className="stat-number">95.1%</span>
                    <span className="stat-label">F1 Score</span>
                  </div>
                </div>
                <p className="helper" style={{ marginTop: '1rem' }}>
                  n=163 stratified random sample (seed=42), MedGemma 4B Q4_KM quantized model
                </p>
              </div>

              <div className="about-section">
                <h3>Technical Architecture</h3>
                <ul>
                  <li><strong>MedGemma 4B</strong> — Google's medical multimodal model for vision-language understanding</li>
                  <li><strong>LangGraph Agent</strong> — Orchestrated analysis workflow</li>
                  <li><strong>Hierarchical Decision Logic</strong> — VERACITY_FIRST with optimized thresholds</li>
                  <li><strong>Efficient Deployment</strong> — Quantized 4-bit model runs locally via llama-cpp-python</li>
                </ul>
              </div>

              <div className="about-section">
                <h3>Impact & Deployment</h3>
                <p>
                  Partnership with <strong>HERO Lab, University of British Columbia</strong> (Scientific Director: Jamie Forrest)
                  for deployment to African Ministries of Health and rural clinical settings. Target scale:
                  millions of patients via Telegram bot integration.
                </p>
              </div>

              <div className="about-section about-footer">
                <h3>Project Information</h3>
                <div className="info-grid">
                  <div>
                    <strong>Developer</strong>
                    <p>Jamie Forrest</p>
                  </div>
                  <div>
                    <strong>Affiliation</strong>
                    <p>HERO Lab, School of Nursing<br/>University of British Columbia</p>
                  </div>
                  <div>
                    <strong>Contact</strong>
                    <p>
                      <a href="mailto:james.forrest@ubc.ca">james.forrest@ubc.ca</a><br/>
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
                  <strong>Date:</strong> February 2026 | <strong>Model:</strong> MedGemma 4B Q4_KM | <strong>Dataset:</strong> Med-MMHL (n=163)
                </p>
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

export default SettingsAndTools
