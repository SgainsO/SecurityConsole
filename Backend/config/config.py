from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    MONGODB_STRING: str = os.getenv("MONGODB_URI", "")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "security_console")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")

    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create a singleton instance
settings = Settings()