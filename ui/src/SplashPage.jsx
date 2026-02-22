import { useState, useCallback } from 'react'
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
      'MedContext sees that both the photo and the caption look plausible, but together they don\'t match \u2014 it recognises a caterpillar, not a virus.',
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
      'MedContext detects it\u2019s actually a digital illustration, so the image and the claim about experimental data are inconsistent.',
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
      'MedContext confirms the lines on the cassette match the clinical interpretation, so it treats this image\u2013claim pair as trustworthy.',
    veracity: 'Accurate',
    alignment: 'Aligned',
  },
]

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
            by analyzing whether claims match their images &mdash; not just
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
                >
                  <div
                    className={`card-inner ${isFlipped ? 'card-flipped' : ''}`}
                  >
                    {/* Front — image + claim only, no verdict */}
                    <div className="card-front">
                      <img
                        src={card.image}
                        alt={`Demo: ${card.claim.slice(0, 40)}...`}
                        className="card-image"
                      />
                      <div className="card-overlay">
                        <p className="card-claim">&ldquo;{card.claim}&rdquo;</p>
                        <p className="card-flip-hint">Tap to reveal verdict</p>
                      </div>
                    </div>

                    {/* Back — verdict + analysis */}
                    <div className="card-back">
                      <span
                        className={`verdict-badge ${
                          card.verdict === 'misinformation'
                            ? 'verdict-misinfo'
                            : 'verdict-legit'
                        }`}
                      >
                        {card.badgeLabel}
                      </span>
                      <h3>{card.backTitle}</h3>
                      <p className="card-back-text">{card.backText}</p>
                      <div className="signal-bars">
                        <div className="signal-row">
                          <span className="signal-label">Veracity</span>
                          <span
                            className={`signal-value ${
                              card.veracity === 'Accurate'
                                ? 'signal-high'
                                : 'signal-medium'
                            }`}
                          >
                            {card.veracity}
                          </span>
                        </div>
                        <div className="signal-row">
                          <span className="signal-label">Alignment</span>
                          <span
                            className={`signal-value ${
                              card.alignment === 'Aligned'
                                ? 'signal-high'
                                : 'signal-low'
                            }`}
                          >
                            {card.alignment}
                          </span>
                        </div>
                      </div>
                      <p className="card-back-hint">Click to flip back</p>
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

        {/* Carousel dots */}
        <div className="carousel-dots">
          {DEMO_CARDS.map((card, index) => (
            <button
              key={card.id}
              type="button"
              className={`carousel-dot ${index === centerIndex ? 'carousel-dot-active' : ''}`}
              onClick={() => {
                setFlippedCards({})
                setCenterIndex(index)
              }}
              aria-label={`Go to card ${index + 1}`}
            />
          ))}
        </div>
      </section>

      {/* Video + Description Section */}
      <section className="card splash-video-section">
        <h2 className="splash-section-title">See It In Action</h2>
        <p className="splash-section-subtitle">
          Watch how MedContext analyzes real medical misinformation in under two minutes.
        </p>
        <div className="video-embed-wrapper">
          {/* Replace YOUR_VIDEO_ID with the actual YouTube video ID */}
          <div className="video-embed-placeholder">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            <p>YouTube video embed goes here</p>
            <p className="helper">
              Replace the placeholder in SplashPage.jsx with:<br />
              <code>&lt;iframe src=&quot;https://www.youtube.com/embed/YOUR_VIDEO_ID&quot; ...&gt;</code>
            </p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="card splash-how">
        <h2 className="splash-section-title">How It Works</h2>
        <div className="how-steps">
          <div className="how-step">
            <div className="how-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <polyline points="21 15 16 10 5 21" />
              </svg>
            </div>
            <h3>Submit Image + Claim</h3>
            <p>Upload a medical image and the claim being made about it.</p>
          </div>
          <div className="how-arrow">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </div>
          <div className="how-step">
            <div className="how-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2a10 10 0 1 0 10 10" />
                <path d="M12 12l7-7" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </div>
            <h3>AI Analyzes Context</h3>
            <p>MedGemma assesses claim veracity and image-claim alignment.</p>
          </div>
          <div className="how-arrow">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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

      {/* Validation Teaser */}
      <section className="card splash-teaser">
        <p className="teaser-text">
          We tested <strong>3 MedGemma variants</strong> &mdash; 4B instruction-tuned,
          4B pre-trained, and 4B quantized (Q4_KM) &mdash; on 163 real-world medical claims.
          Which model catches the most misinformation?
        </p>
        <button
          type="button"
          className="teaser-cta"
          onClick={onNavigateToValidation}
        >
          See the Results
        </button>
      </section>

      {/* Stats Bar */}
      <section className="card splash-stats">
        <div className="stat-item">
          <span className="stat-value">94.5%</span>
          <span className="stat-label">Avg. Veracity + Alignment Accuracy</span>
        </div>
        <div className="stat-divider" />
        <div className="stat-item">
          <span className="stat-value">163</span>
          <span className="stat-label">Real-World Examples Tested</span>
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
