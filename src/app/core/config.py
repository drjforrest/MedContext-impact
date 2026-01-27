from pydantic import AliasChoices, ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/medcontext"
    redis_url: str = "redis://localhost:6379"
    medgemma_url: str = "http://localhost:8001"
    medgemma_provider: str = "huggingface"  # huggingface | local | vllm | vertex
    medgemma_hf_model: str = "google/medgemma-1.5-4b-it"
    medgemma_hf_token: str = Field(
        default="",
        validation_alias=AliasChoices("MEDGEMMA_HF_TOKEN"),
    )
    medgemma_max_new_tokens: int = Field(
        default=2000,
        validation_alias=AliasChoices("MEDGEMMA_MAX_NEW_TOKENS"),
    )
    medgemma_vllm_url: str = "http://localhost:8001/v1/chat/completions"
    medgemma_vertex_project: str = ""
    medgemma_vertex_location: str = "us-central1"
    medgemma_vertex_endpoint: str = ""
    medgemma_fallback_provider: str = Field(
        default="local",
        validation_alias=AliasChoices("MEDGEMMA_FALLBACK_PROVIDER"),
    )
    llm_provider: str = "openai_compatible"  # openai_compatible | ollama
    llm_orchestrator: str = "openai/gpt-4o-mini"
    llm_worker: str = "openai/gpt-4o-mini"
    llm_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "LLM_API_KEY",
            "OPENROUTER_API_KEY",
            "GOOGLE_API_KEY",
            "VERTEX_API_KEY",
            "vertex_ai_api_key",
        ),
    )
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_timeout_seconds: float = 60.0
    serp_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("SERP_API_KEY"),
    )
    serp_api_timeout_seconds: float = 20.0
    tineye_api_key: str = ""
    google_vision_api_key: str = ""
    whatsapp_business_api_key: str = ""
    telegram_bot_token: str = Field(
        default="",
        validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN"),
    )
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = ""
    reddit_subreddits: str = ""
    reddit_keywords: str = ""
    reddit_poll_interval_minutes: int = 60
    enable_monitoring_polling: bool = False
    jwt_secret: str = ""
    encryption_key: str = ""
    log_level: str = "INFO"
    image_storage_dir: str = "data/images"
    appwrite_project_id: str = Field(
        default="",
        validation_alias=AliasChoices("VITE_APPWRITE_PROJECT_ID", "vite_appwrite_project_id"),
    )
    appwrite_project_name: str = Field(
        default="",
        validation_alias=AliasChoices(
            "VITE_APPWRITE_PROJECT_NAME", "vite_appwrite_project_name"
        ),
    )
    appwrite_endpoint: str = Field(
        default="",
        validation_alias=AliasChoices("VITE_APPWRITE_ENDPOINT", "vite_appwrite_endpoint"),
    )

    model_config = ConfigDict(env_file=".env")


settings = Settings()
