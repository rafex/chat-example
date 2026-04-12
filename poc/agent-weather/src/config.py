import os
from typing import Optional
from dotenv import load_dotenv

# Calcular la ruta al archivo .env (poc/.env)
current_dir = os.path.dirname(os.path.abspath(__file__))
agent_weather_src = current_dir  # poc/agent-weather/src
agent_weather_root = os.path.dirname(agent_weather_src)  # poc/agent-weather
project_root = os.path.dirname(agent_weather_root)  # poc
env_path = os.path.join(project_root, '.env')

# Cargar variables de entorno desde poc/.env
load_dotenv(dotenv_path=env_path)

class Config:
    # OpenWeatherMap API
    OPENWEATHER_API_KEY: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    
    # Configuración de Proveedores LLM (seleccionable por comando)
    # Las claves individuales se leen desde .env
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini") # GPT-4o-mini es rápido y barato
    
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free")
    
    # Proveedor actual (por defecto OpenRouter si está configurado, sino OpenAI)
    CURRENT_LLM_PROVIDER: str = os.getenv("CURRENT_LLM_PROVIDER", "openrouter")

    @classmethod
    def get_current_config(cls):
        """Obtiene la configuración del proveedor LLM actualmente seleccionado"""
        provider = cls.CURRENT_LLM_PROVIDER.lower()
        
        if provider == "openai":
            return {
                "api_key": cls.OPENAI_API_KEY,
                "base_url": cls.OPENAI_BASE_URL,
                "model": cls.OPENAI_MODEL
            }
        elif provider == "deepseek":
            return {
                "api_key": cls.DEEPSEEK_API_KEY,
                "base_url": cls.DEEPSEEK_BASE_URL,
                "model": cls.DEEPSEEK_MODEL
            }
        elif provider == "openrouter":
            return {
                "api_key": cls.OPENROUTER_API_KEY,
                "base_url": cls.OPENROUTER_BASE_URL,
                "model": cls.OPENROUTER_MODEL
            }
        else:
            # Fallback a OpenAI
            return {
                "api_key": cls.OPENAI_API_KEY,
                "base_url": cls.OPENAI_BASE_URL,
                "model": cls.OPENAI_MODEL
            }

    @classmethod
    def set_provider(cls, provider: str):
        """Cambia el proveedor LLM actual"""
        cls.CURRENT_LLM_PROVIDER = provider
        # Podríamos guardar esto en un archivo temporal o variable de entorno si se desea persistencia
        print(f"Proveedor LLM cambiado a: {provider}")

    @classmethod
    def validate(cls):
        if not cls.OPENWEATHER_API_KEY:
            raise ValueError("OPENWEATHER_API_KEY no está configurada en variables de entorno")
        return True
