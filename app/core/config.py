from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Kanban API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Reemplaza las configuraciones de la base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://bd-planning_owner:npg_JXqi4ph0wWVy@ep-young-firefly-a5ci8ouj-pooler.us-east-2.aws.neon.tech/bd-planning?sslmode=require")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    class Config:
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

# Asegúrate de que DATABASE_URL no sea None
if not Settings().DATABASE_URL:
    raise ValueError("DATABASE_URL no está configurada en el archivo .env") 