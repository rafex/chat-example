import os
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    # OpenWeatherMap API
    OPENWEATHER_API_KEY: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    
    # Proveedor LLM Genérico (compatible con OpenAI)
    # Permite usar DeepSeek, OpenAI, u otros proveedores con API OpenAI-compatible
    LLM_PROVIDER_API_KEY: Optional[str] = os.getenv("LLM_PROVIDER_API_KEY")
    LLM_PROVIDER_API_BASE: str = os.getenv(
        "LLM_PROVIDER_API_BASE", 
        "https://api.deepseek.com/v1"
    )
    LLM_PROVIDER_MODEL: str = os.getenv("LLM_PROVIDER_MODEL", "deepseek-chat")
    
    # Backward compatibility: variables antiguas de DeepSeek
    @classmethod
    def get_llm_api_key(cls) -> Optional[str]:
        """Obtiene la API key del LLM (soporta variables antiguas y nuevas)"""
        return (cls.LLM_PROVIDER_API_KEY or 
                os.getenv("DEEPSEEK_API_KEY") or 
                os.getenv("OPENAI_API_KEY"))

    @classmethod
    def get_llm_api_base(cls) -> str:
        """Obtiene la URL base del LLM"""
        return (cls.LLM_PROVIDER_API_BASE or 
                os.getenv("DEEPSEEK_API_BASE") or 
                os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"))

    @classmethod
    def get_llm_model(cls) -> str:
        """Obtiene el modelo del LLM"""
        return (cls.LLM_PROVIDER_MODEL or 
                os.getenv("DEEPSEEK_MODEL") or 
                os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"))

    @classmethod
    def validate(cls):
        if not cls.OPENWEATHER_API_KEY:
            raise ValueError("OPENWEATHER_API_KEY no está configurada en variables de entorno")
        return True
