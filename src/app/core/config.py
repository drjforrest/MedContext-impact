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
    medgemma_vertex_dedicated_domain: str = ""
    vertexai_api_key: str = Field(
        default="",
        validation_alias=AliasChoices(
            "VERTEX_API_KEY", "VERTEXAI_API_KEY", "VERTEX_AI_API_KEY"
        ),
    )
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
    google_vision_api_key: str = ""
    telegram_bot_token: str = Field(
        default="",
        validation_alias=AliasChoices("TELEGRAM_BOT_TOKEN"),
    )
    enable_forensics: bool = False
    enable_forensics_medgemma: bool = False
    jwt_secret: str = ""
    encryption_key: str = ""
    log_level: str = "INFO"
    image_storage_dir: str = "data/images"
    demo_access_code: str = Field(
        default="",
        validation_alias=AliasChoices("DEMO_ACCESS_CODE"),
    )
    appwrite_project_id: str = Field(
        default="",
        validation_alias=AliasChoices(
            "APPWRITE_PROJECT_ID",
            "appwrite_project_id",
            "VITE_APPWRITE_PROJECT_ID",
            "vite_appwrite_project_id",
        ),
    )
    appwrite_project_name: str = Field(
        default="",
        validation_alias=AliasChoices(
            "APPWRITE_PROJECT_NAME",
            "appwrite_project_name",
            "VITE_APPWRITE_PROJECT_NAME",
            "vite_appwrite_project_name",
        ),
    )
    appwrite_endpoint: str = Field(
        default="",
        validation_alias=AliasChoices(
            "APPWRITE_ENDPOINT",
            "appwrite_endpoint",
            "VITE_APPWRITE_ENDPOINT",
            "vite_appwrite_endpoint",
        ),
    )

    model_config = ConfigDict(env_file=".env")


settings = Settings()
