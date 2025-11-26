from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings - .env se load hogi"""
    
    # Google Gemini API (not OpenAI!)
    google_api_key: str  # Required for Gemini
    llm_model: str = "gemini-2.0-flash"  # Free tier model
    llm_temperature: float = 0.7
    
    # Alpaca Settings
    alpaca_api_key: str
    alpaca_api_secret: str
    alpaca_base_url: str = "https://paper-api.alpaca.markets/v2"
    
    # Tavily Settings
    tavily_api_key: str
    
    # Agent Settings
    max_retries: int = 3
    anomaly_threshold: float = 10.0
    volume_threshold: float = 3.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
