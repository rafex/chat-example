import os
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    OPENWEATHER_API_KEY: Optional[str] = os.getenv("OPENWEATHER_API_KEY")
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org/data/2.5"

    @classmethod
    def validate(cls):
        if not cls.OPENWEATHER_API_KEY:
            raise ValueError("OPENWEATHER_API_KEY no está configurada en variables de entorno")
        return True
