import { useCallback, useState } from 'react'
import './SplashPage.css'

const DEMO_CARDS = [
  {
    id: 1,
    image: '/demo/demo_image_001.png',
    claim: 'For those who have never seen the HIV virus magnified under an electronic microscope, here it is now.',
    verdict: 'misinformation',
    badgeLabel: 'MISINFORMATION DETECTED',
    backTitle: 'MedContext Analysis',
    backText:
      'MedContext sees that both the photo and the caption look plausible, but together they don\'t match — it recognises a caterpillar, not a virus.',
    veracity: 'Plausible',
    alignment: 'Misaligned',
  },
  {
    id: 2,
    image: '/demo/demo_image_002.jpg',
    claim: 'The most detailed image of a human cell to date, obtained using X-ray, nuclear magnetic resonance, and cryo-electron microscopy datasets.',
    verdict: 'misinformation',
    badgeLabel: 'MISINFORMATION DETECTED',
    backTitle: 'MedContext Analysis',
    backText:
      'MedContext detects it\'s actually a digital illustration, so the image and the claim about experimental data are inconsistent.',
    veracity: 'Plausible',
    alignment: 'Misaligned',
  },
  {
    id: 3,
    image: '/demo/demo_image_003.jpg',
    claim: 'Positive malaria rapid diagnostic test showing Plasmodium falciparum infection.',
    verdict: 'verified',
    badgeLabel: 'VERIFIED',
    backTitle: 'MedContext Analysis',
    backText:
      'MedContext confirms the lines on the cassette match the clinical interpretation, so it treats this image–claim pair as trustworthy.',
    veracity: 'Accurate',
    alignment: 'Aligned',
  },
]

// FRESH VALIDATION DATA - February 20, 2026
const VALIDATION_DATA = {
  q: {
    model: "MedGemma 4B IT Q4_KM",
    date: "February 20, 2026",
    veracity: 71.2,
    alignment: 77.9,
    combined: {
      accuracy: 91.4,
      precision: 96.9,
      recall: 92.6,
      f1: 94.7,
      tp: 125, fp: 4, tn: 24, fn: 10,
    },
    thresholds: { veracity: 0.65, alignment: 0.30 },
  },
  dataset: { n: 163, misinfo: 136, legitimate: 27 },
}

// YouTube video URL
const VIDEO_URL = 'https://youtu.be/uoD6gL2l934'

function SplashPage({ onNavigateToVerify, onNavigateToValidation }) {
  const [centerIndex, setCenterIndex] = useState(0)
  const [flippedCards, setFlippedCards] = useState({})

  const rotateLeft = useCallback(() => {
    setFlippedCards({})
    setCenterIndex((prev) => (prev - 1 + DEMO_CARDS.length) % DEMO_CARDS.length)
  }, [])

  const rotateRight = useCallback(() => {
    setFlippedCards({})
    setCenterIndex((prev) => (prev + 1) % DEMO_CARDS.length)
  }, [])

  const toggleFlip = useCallback((cardId) => {
    setFlippedCards((prev) => ({
      ...prev,
      [cardId]: !prev[cardId],
    }))
  }, [])

  const getCardPosition = (index) => {
    const diff = (index - centerIndex + DEMO_CARDS.length) % DEMO_CARDS.length
    if (diff === 0) return 'center'
    if (diff === 1) return 'right'
    return 'left'
  }

  const d = VALIDATION_DATA.q

  return (
    <div className="splash">
      {/* Hero Section */}
      <section className="card splash-hero">
        <div className="splash-banner-frame">
          <img
            className="splash-banner"
            src="/images/splash-page-banner.png"
            alt="MedContext"
          />
        </div>
        <div className="splash-hero-inner">
          <h1 className="splash-headline">
            Medical images don&apos;t need to be fake to cause harm.
          </h1>
          <p className="splash-subtitle">
            MedContext is an AI-powered tool that detects medical misinformation
            by analyzing whether claims match their images — not just
            whether images are doctored.
          </p>
          <div className="splash-cta">
            <button type="button" onClick={onNavigateToVerify}>
              Try It Now
            </button>
            <button
              type="button"
              className="ghost"
              onClick={onNavigateToValidation}
            >
              See the Evidence
            </button>
          </div>
        </div>
      </section>

      {/* Video Section */}
      <section className="card splash-video">
        <h2 className="splash-section-title">See MedContext in Action</h2>
        <div className="video-container">
          <iframe
            width="100%"
            height="400"
            src={VIDEO_URL}
            title="MedContext Demo"
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
          />
        </div>
      </section>

      {/* Card Carousel Section */}
      <section className="splash-carousel-section">
        <h2 className="splash-section-title">Real Examples. Real Threats.</h2>
        <p className="splash-section-subtitle">
          Click a card to reveal MedContext&apos;s analysis.
        </p>

        <div className="carousel-wrapper">
          <button
            type="button"
            className="carousel-arrow carousel-arrow-left"
            onClick={rotateLeft}
            aria-label="Previous card"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
          </button>

          <div
            className="carousel-stage"
            role="region"
            aria-label={`Demo example ${centerIndex + 1} of ${DEMO_CARDS.length}`}
            aria-live="polite"
          >
            {DEMO_CARDS.map((card, index) => {
              const position = getCardPosition(index)
              const isFlipped = flippedCards[card.id] || false
              const isCenter = position === 'center'

              return (
                <div
                  key={card.id}
                  className={`carousel-card carousel-card-${position}`}
                  onClick={isCenter ? () => toggleFlip(card.id) : undefined}
                  role={isCenter ? 'button' : undefined}
                  tabIndex={isCenter ? 0 : -1}
                  onKeyDown={
                    isCenter
                      ? (e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault()
                            toggleFlip(card.id)
                          }
                        }
                      : undefined
                  }
                  aria-label={isCenter ? `Example ${index + 1}: ${card.claim}. Click to flip.` : undefined}
                >
                  <div className={`flipper ${isFlipped ? 'flipped' : ''}`}>
                    {/* Front */}
                    <div className="card-face card-front">
                      <div className="card-image-wrapper">
                        <img src={card.image} alt={`Example ${index + 1}`} />
                      </div>
                      <div className="card-content-front">
                        <p className="card-claim">{card.claim}</p>
                        <span className={`verdict-badge ${card.verdict}`}>
                          {card.badgeLabel}
                        </span>
                      </div>
                    </div>

                    {/* Back */}
                    <div className="card-face card-back">
                      <div className="card-content-back">
                        <h4>{card.backTitle}</h4>
                        <p>{card.backText}</p>
                        <div className="analysis-details">
                          <div className="analysis-item">
                            <span className="analysis-label">Veracity:</span>
                            <span className="analysis-value">{card.veracity}</span>
                          </div>
                          <div className="analysis-item">
                            <span className="analysis-label">Alignment:</span>
                            <span className="analysis-value">{card.alignment}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          <button
            type="button"
            className="carousel-arrow carousel-arrow-right"
            onClick={rotateRight}
            aria-label="Next card"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </button>
        </div>
      </section>

      {/* How It Works */}
      <section className="card splash-how">
        <h2 className="splash-section-title">How MedContext Works</h2>
        <div className="how-grid">
          <div className="how-step">
            <div className="how-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <polyline points="21 15 16 10 5 21" />
              </svg>
            </div>
            <h3>Upload Image</h3>
            <p>Share a medical image and accompanying claim.</p>
          </div>
          <div className="how-arrow">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </div>
          <div className="how-step">
            <div className="how-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-purple)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                <line x1="12" y1="22.08" x2="12" y2="12" />
              </svg>
            </div>
            <h3>Analyze Context</h3>
            <p>AI examines veracity (claim truth) and alignment (image-claim match).</p>
          </div>
          <div className="how-arrow">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </div>
          <div className="how-step">
            <div className="how-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-green)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <h3>Get Verdict</h3>
            <p>Receive a clear misinformation verdict with rationale.</p>
          </div>
        </div>
      </section>

      {/* S-Curve Validation Teaser */}
      <section className="card splash-teaser" style={{ background: 'linear-gradient(135deg, rgba(42, 157, 143, 0.1) 0%, rgba(45, 184, 138, 0.05) 100%)' }}>
        <p className="teaser-text">
          We tested MedContext on <strong>163 real health-related image-claim pairs</strong> from the Med-MMHL benchmark.
          Individual signals achieved only 71-78% accuracy — but <strong>combined optimization 
          unlocks 91.4%</strong>. See the S-curve breakthrough.
        </p>
        <button
          type="button"
          className="teaser-cta"
          onClick={onNavigateToValidation}
        >
          See the Results
        </button>
      </section>

      {/* Stats Bar with S-Curve Data */}
      <section className="card splash-stats">
        <div className="stat-item">
          <span className="stat-value" style={{ color: '#E63946' }}>{(d.veracity || 0).toFixed(0)}%</span>
          <span className="stat-label">Veracity Only</span>
        </div>
        <div className="stat-divider" />
        <div className="stat-item">
          <span className="stat-value" style={{ color: '#F4A261' }}>{(d.alignment || 0).toFixed(0)}%</span>
          <span className="stat-label">Alignment Only</span>
        </div>
        <div className="stat-divider" />
        <div className="stat-item" style={{ background: 'rgba(42, 157, 143, 0.1)', padding: '0.5rem 1rem', borderRadius: '8px' }}>
          <span className="stat-value" style={{ color: '#2A9D8F', fontSize: '2.2rem' }}>{(d.combined?.accuracy || 0).toFixed(1)}%</span>
          <span className="stat-label"><strong>Optimized</strong></span>
        </div>
        <div className="stat-divider" />
        <div className="stat-item">
          <span className="stat-value">{d.n}</span>
          <span className="stat-label">Test Samples</span>
        </div>
        <div className="stat-divider" />
        <div
          className="stat-item stat-item-link"
          onClick={onNavigateToValidation}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault()
              onNavigateToValidation()
            }
          }}
        >
          <span className="stat-value">Med-MMHL</span>
          <span className="stat-label">Benchmark &rarr;</span>
        </div>
      </section>
    </div>
  )
}

export default SplashPage