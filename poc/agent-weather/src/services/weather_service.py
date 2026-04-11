import requests
from typing import Optional
from src.schemas.weather import WeatherData
from src.config import Config

class WeatherService:
    """Servicio para consumir la API de OpenWeatherMap"""

    def __init__(self):
        Config.validate()
        self.api_key = Config.OPENWEATHER_API_KEY
        self.base_url = Config.OPENWEATHER_BASE_URL

    def get_weather(self, location: str) -> WeatherData:
        """
        Obtiene datos climáticos para una ubicación específica.

        Args:
            location: Nombre de la ciudad o ubicación

        Returns:
            WeatherData: Modelo de datos validado con Pydantic

        Raises:
            ValueError: Si la ubicación es inválida o la API falla
        """
        try:
            endpoint = f"{self.base_url}/weather"
            params = {
                "q": location,
                "appid": self.api_key,
                "lang": "es"
            }

            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()

            # Parsear y validar la respuesta con Pydantic
            weather_data = WeatherData(**response.json())
            return weather_data

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error al consultar API de clima: {str(e)}")

    def get_weather_by_coords(self, lat: float, lon: float) -> WeatherData:
        """
        Obtiene datos climáticos usando coordenadas geográficas.

        Args:
            lat: Latitud
            lon: Longitud

        Returns:
            WeatherData: Modelo de datos validado con Pydantic
        """
        try:
            endpoint = f"{self.base_url}/weather"
            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "lang": "es"
            }

            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()

            weather_data = WeatherData(**response.json())
            return weather_data

        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error al consultar API de clima: {str(e)}")
