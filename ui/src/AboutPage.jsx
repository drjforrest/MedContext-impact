import './AboutPage.css'

function AboutPage() {
  return (
    <div className="about-page">
      <section className="card about-page-card">
        <h1>About MedContext</h1>

        <p className="about-page-text">
          MedContext was developed by Jamie Forrest for submission to the Kaggle Google MedGemma Impact Challenge submitted on
          February 23, 2026. MedContext is an agentic AI application that uses the multimodal
          MedGemma model to detect medical misinformation by testing image-claim pair contextual
          authenticity.
        </p>

        <p className="about-page-text">
          MedContext is a suite of AI-powered tools that also contains modules for image integrity
          (pixel forensics) not demonstrated here, as well as modules for source verification, and
          provenance blockchain audit logging (in development).
        </p>

        <p className="about-page-text">
          MedContext is currently deployed in production with the MedGemma Q4_K_M quantized variant
          with CPU-only inference. It can however, be easily configured to run the full 4B
          instruction-tuned or pre-trained variants with GPU acceleration at a dedicated endpoint
          with configurable options for inference provider with HuggingFace or Google Vertex AI.
        </p>

        <p className="about-page-text">
          MedContext also ships with a Telegram bot for field use deployment. In partnership with
          Counterforce AI (
          <a href="https://counterforce.tech" target="_blank" rel="noopener noreferrer">
            counterforce.tech
          </a>
          ) and the University of British Columbia Health Equity and Resilience Observatory, it
          will continue development and evaluation for maximum impact on minimizing the harms of
          medical misinformation.
        </p>

        <p className="about-page-text">
          For more information on MedContext, please contact the developer on{' '}
          <a href="https://github.com/drjforrest" target="_blank" rel="noopener noreferrer">
            Github
          </a>.
        </p>
      </section>
    </div>
  )
}

export default AboutPage
