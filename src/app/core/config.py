from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/medcontext"
    redis_url: str = "redis://localhost:6379"
    medgemma_url: str = "http://localhost:8001"
    medgemma_provider: str = "huggingface"  # huggingface | vertex
    medgemma_hf_model: str = "google/medgemma-2b-finetuned"
    medgemma_hf_token: str = ""
    medgemma_vertex_project: str = ""
    medgemma_vertex_location: str = "us-central1"
    medgemma_vertex_endpoint: str = ""
    tineye_api_key: str = ""
    google_vision_api_key: str = ""
    whatsapp_business_api_key: str = ""
    jwt_secret: str = ""
    encryption_key: str = ""
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
