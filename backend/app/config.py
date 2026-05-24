from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: str = "development"
    app_name: str = "VitalAI"
    app_version: str = "0.1.0"
    synthetic_only: bool = True

    # Database
    database_url: str

    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    login_rate_limit: str = "5/minute"

    # LLM
    llm_provider: str = "ollama"
    llm_model: str = "gemma2:9b"
    ollama_base_url: str = "http://ollama:11434"

    # Bedrock
    aws_region: str = "ap-southeast-2"
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"


settings = Settings()
