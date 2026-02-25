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
            MedContext detects medical misinformation by analyzing whether claims match their images.
            No signal is good enough alone; the veracity fallback catches millions at scale&mdash;only
            possible with MedContext&apos;s multimodal medical training.
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

      {/* Video Section - MOVED UP */}
      <section className="card splash-video-section">
        <h2 className="splash-section-title">See It In Action</h2>
        <p className="splash-section-subtitle">
          Watch how MedContext analyzes real medical misinformation in under three minutes.
        </p>
        <div className="video-embed-wrapper">
          <iframe
            width="100%"
            height="100%"
            src="https://www.youtube.com/embed/4NuGsrnuVk8?rel=0&modestbranding=1"
            title="MedContext Demo"
            frameBorder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
            referrerPolicy="strict-origin-when-cross-origin"
            allowFullScreen
          />
        </div>
        <a
          href="https://www.youtube.com/watch?v=4NuGsrnuVk8&feature=youtu.be"
          target="_blank"
          rel="noopener noreferrer"
          className="splash-watch-youtube-link"
        >
          Watch on YouTube
        </a>
      </section>

      {/* Card Carousel Section - MOVED DOWN */}
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

      {/* Why This Matters - Use Cases */}
      <section className="card splash-why-matters">
        <h2 className="splash-section-title">Why This Matters</h2>
        <p className="splash-section-subtitle">
          Medical misinformation can cost lives. Here&apos;s where MedContext makes a real-world impact.
        </p>

        <div className="use-cases">
          <div className="use-case">
            <div className="use-case-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#5a8ab8" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 8h1a4 4 0 0 1 0 8h-1" />
                <path d="M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z" />
                <line x1="6" y1="1" x2="6" y2="4" />
                <line x1="10" y1="1" x2="10" y2="4" />
                <line x1="14" y1="1" x2="14" y2="4" />
              </svg>
            </div>
            <h3>Public Health Crises</h3>
            <p>During pandemics, unrelated medical images get repurposed with false claims about new diseases. MedContext detects when a chest X-ray labeled as "new COVID variant" is actually tuberculosis from 2015.</p>
            <div className="impact-stat">
              <span className="impact-number">Viral spread</span>
              <span className="impact-label">of repurposed medical imagery</span>
            </div>
          </div>

          <div className="use-case">
            <div className="use-case-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#4a7fb5" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
                <path d="M12 7v5" />
                <path d="M9.5 9.5l5 5" />
                <path d="M14.5 9.5l-5 5" />
              </svg>
            </div>
            <h3>Journalism &amp; Fact-Checking</h3>
            <p>Journalists racing to verify viral medical claims during public health emergencies need rapid, reliable tools. MedContext helps newsrooms distinguish legitimate medical evidence from contextually misleading imagery before publication.</p>
            <div className="impact-stat">
              <span className="impact-number">Real-time</span>
              <span className="impact-label">verification during breaking news</span>
            </div>
          </div>

          <div className="use-case">
            <div className="use-case-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent-teal)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
              </svg>
            </div>
            <h3>Social Media Moderation</h3>
            <p>Platforms struggle to verify medical content at scale. A "miracle cure" post with legitimate medical imaging but fraudulent claims needs human expertise &mdash; or MedContext's automated analysis.</p>
            <div className="impact-stat">
              <span className="impact-number">At scale</span>
              <span className="impact-label">automated content verification</span>
            </div>
          </div>

          <div className="use-case">
            <div className="use-case-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent-blue)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
            </div>
            <h3>Clinical Decision Support</h3>
            <p>Healthcare providers encounter medical images shared by patients from unreliable sources. MedContext helps clinicians quickly assess whether patient-provided "diagnostic evidence" is contextually accurate.</p>
            <div className="impact-stat">
              <span className="impact-number">Point of care</span>
              <span className="impact-label">verification for clinicians</span>
            </div>
          </div>

          <div className="use-case">
            <div className="use-case-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#3d6fa0" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                <path d="M12 6v6" />
                <path d="M9 9h6" />
              </svg>
            </div>
            <h3>Medical Education</h3>
            <p>Students, residents, and lifelong learners encounter mislabeled or misrepresented medical images in textbooks, online courses, and study forums. MedContext ensures educational materials accurately represent the pathology they claim to illustrate.</p>
            <div className="impact-stat">
              <span className="impact-number">91.4%</span>
              <span className="impact-label">accuracy on Med-MMHL benchmark</span>
            </div>
          </div>

          <div className="use-case">
            <div className="use-case-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#2d5f8d" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 16v-4" />
                <path d="M12 8h.01" />
              </svg>
            </div>
            <h3>Public Health Communication</h3>
            <p>Health agencies and NGOs need to ensure their outreach materials use medically accurate imagery that aligns with their messaging. Mismatched image-claim pairs undermine trust in public health guidance and vaccine campaigns.</p>
            <div className="impact-stat">
              <span className="impact-number">Trust</span>
              <span className="impact-label">through accuracy and transparency</span>
            </div>
          </div>
        </div>

        <div className="why-cta-wrapper">
          <button
            type="button"
            className="teaser-cta"
            onClick={onNavigateToVerify}
          >
            Try It Now
          </button>
          <button
            type="button"
            className="teaser-cta ghost"
            onClick={onNavigateToValidation}
          >
            See the Validation Results
          </button>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="card splash-stats">
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%' }}>
          <p style={{ textAlign: 'center', fontSize: '0.9rem', color: '#9ba0af', marginBottom: '1rem', maxWidth: '560px' }}>
            No signal good enough alone. Veracity fallback catches millions at scale&mdash;only possible with MedContext&apos;s multimodal medical training.
          </p>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '2rem', flexWrap: 'wrap' }}>
            <div className="stat-item">
              <span className="stat-value stat-value-red">73.6%</span>
              <span className="stat-label">Veracity Alone</span>
            </div>
            <div className="stat-divider" />
            <div className="stat-item">
              <span className="stat-value stat-value-orange">90.8%</span>
              <span className="stat-label">Alignment Alone</span>
            </div>
            <div className="stat-divider" />
            <div className="stat-item">
              <span className="stat-value stat-value-green">91.4%</span>
              <span className="stat-label">Combined</span>
            </div>
            <div className="stat-divider" />
            <div className="stat-item">
              <span className="stat-value stat-value-purple">163</span>
              <span className="stat-label">Samples</span>
            </div>
            <div className="stat-divider" />
            <div
              className="stat-item stat-item-link stat-item-benchmark"
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
              <span className="stat-value stat-benchmark-name stat-value-blue">Med-MMHL</span>
              <span className="stat-label">Benchmark</span>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}

export default SplashPage
