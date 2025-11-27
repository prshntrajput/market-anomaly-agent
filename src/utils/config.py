from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # Google Gemini API
    google_api_key: str
    llm_model: str = "gemini-2.0-flash"
    llm_temperature: float = 0.7
    
    # Alpaca Settings (optional now)
    alpaca_api_key: Optional[str] = None
    alpaca_api_secret: Optional[str] = None
    alpaca_base_url: str = "https://paper-api.alpaca.markets/v2"
    
    # Tavily Settings
    tavily_api_key: str
    
    # Agent Settings
    max_retries: int = 3
    anomaly_threshold: float = 10.0     # Price change %
    volume_threshold: float = 3.0        # Volume spike ratio
    
    # Monitoring Settings
    monitoring_interval: int = 300       # 5 minutes
    max_anomalies_per_cycle: int = 5     # Max anomalies to investigate per cycle
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
