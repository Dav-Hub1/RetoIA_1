from dotenv import load_dotenv
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env"
    )

    # ========== CONFIGURACIÓN FIJA ==========
    agent_name: str = Field("Manager")
    agent_description: str = Field("Responde preguntas sobre mi experiencia profesional")
    model_name: str = Field("gpt-5-mini")
    embedding_model: str = Field("mistral-embed")
    top_k_retrieval: int = Field(5, description="Número de chunks a recuperar")
    match_function: str = Field("match_cv_analytics")

    # ========== CONFIGURACIÓN SENSIBLE ==========
    supabase_url: str = Field(..., validation_alias="SUPABASE_URL")
    supabase_key: str = Field(..., validation_alias="SUPABASE_KEY")
    supabase_service_key: str = Field(..., validation_alias="SUPABASE_SERVICE_KEY")

    mistral_api_key: str = Field(..., validation_alias="MISTRAL_API_KEY")
    openai_api_key: str = Field(..., validation_alias="OPENAI_API_KEY")

    auth_token: Optional[str] = Field(None, validation_alias="AUTH_TOKEN")

settings = Settings() # type: ignore