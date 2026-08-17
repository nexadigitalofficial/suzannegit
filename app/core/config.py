import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "NEXA PRIME Enterprise Platform"
    VERSION: str = "2.0.0-ENTERPRISE"
    ENVIRONMENT: str = "production"
    
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    
    DATABASE_URL: str = "nexa_database.db"
    
    # Yalnızca ortam değişkeninden okunur (GEMINI_API_KEYS); kodda asla anahtar tutulmaz
    GEMINI_API_KEYS: str = ""
    
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155552671"
    
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://localhost:8050,http://127.0.0.1:8000,http://127.0.0.1:8050"
    
    @property
    def api_keys_list(self) -> List[str]:
        return [k.strip() for k in self.GEMINI_API_KEYS.split(",") if k.strip()]
        
    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
