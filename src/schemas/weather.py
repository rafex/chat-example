from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class WeatherMain(BaseModel):
    temp: float = Field(..., description="Temperatura en Kelvin")
    feels_like: float = Field(..., description="Temperatura sensorial en Kelvin")
    temp_min: float = Field(..., description="Temperatura mínima en Kelvin")
    temp_max: float = Field(..., description="Temperatura máxima en Kelvin")
    pressure: int = Field(..., description="Presión atmosférica en hPa")
    humidity: int = Field(..., description="Humedad en porcentaje")

class WeatherCondition(BaseModel):
    id: int
    main: str
    description: str
    icon: str

class Wind(BaseModel):
    speed: float = Field(..., description="Velocidad del viento en m/s")
    deg: int = Field(..., description="Dirección del viento en grados")

class Clouds(BaseModel):
    all: int = Field(..., description="Nubosidad en porcentaje")

class Sys(BaseModel):
    country: str
    sunrise: int
    sunset: int

class WeatherData(BaseModel):
    coord: dict
    weather: List[WeatherCondition]
    main: WeatherMain
    visibility: int
    wind: Wind
    clouds: Clouds
    dt: int
    sys: Sys
    timezone: int
    id: int
    name: str
    cod: int

    def to_celsius(self) -> float:
        """Convierte temperatura de Kelvin a Celsius"""
        return self.main.temp - 273.15

    def get_weather_summary(self) -> str:
        """Obtiene un resumen del estado del tiempo"""
        condition = self.weather[0] if self.weather else None
        if condition:
            return f"{condition.main}: {condition.description}"
        return "No disponible"

class AnalysisResult(BaseModel):
    location: str
    temperature: float
    temperature_celsius: float
    condition: str
    humidity: int
    wind_speed: float
    recommendations: List[str]
    timestamp: datetime = Field(default_factory=datetime.now)
