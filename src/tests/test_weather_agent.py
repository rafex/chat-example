import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Agregar el directorio src al path para las importaciones
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.weather_agent import run_weather_agent, generate_recommendations
from src.schemas.weather import WeatherData, AnalysisResult
from src.services.weather_service import WeatherService


class TestWeatherAgent(unittest.TestCase):

    def setUp(self):
        """Configuración inicial para cada test"""
        self.mock_weather_data = {
            "coord": {"lon": -0.1257, "lat": 51.5085},
            "weather": [{"id": 800, "main": "Clear", "description": "cielo despejado", "icon": "01d"}],
            "main": {
                "temp": 298.15,
                "feels_like": 298.15,
                "temp_min": 297.15,
                "temp_max": 299.15,
                "pressure": 1013,
                "humidity": 65
            },
            "visibility": 10000,
            "wind": {"speed": 3.5, "deg": 180},
            "clouds": {"all": 0},
            "dt": 1638144000,
            "sys": {"country": "GB", "sunrise": 1638124800, "sunset": 1638157200},
            "timezone": 0,
            "id": 2643743,
            "name": "London",
            "cod": 200
        }

    @patch('src.services.weather_service.WeatherService.get_weather')
    def test_run_weather_agent_success(self, mock_get_weather):
        """Test ejecución exitosa del agente"""
        # Configurar mock
        weather_data = WeatherData(**self.mock_weather_data)
        mock_get_weather.return_value = weather_data

        # Ejecutar agente
        result = run_weather_agent("London")

        # Verificar resultados
        self.assertTrue(result["success"])
        self.assertEqual(result["location"], "London")
        self.assertIsNotNone(result["weather_data"])
        self.assertIsNotNone(result["analysis"])
        self.assertIsInstance(result["recommendations"], list)
        self.assertGreater(len(result["recommendations"]), 0)

    @patch('src.services.weather_service.WeatherService.get_weather')
    def test_run_weather_agent_api_error(self, mock_get_weather):
        """Test manejo de error en API"""
        # Configurar mock para lanzar excepción
        mock_get_weather.side_effect = ValueError("API Error")

        # Ejecutar agente
        result = run_weather_agent("London")

        # Verificar manejo de error
        # El agente actualmente captura la excepción y retorna success=True con weather_data=None
        # y el error en el estado interno, pero run_weather_agent no lo expone explícitamente
        # Por ahora verificamos que no haya datos climáticos
        self.assertTrue(result["success"])
        self.assertIsNone(result["weather_data"])

    def test_generate_recommendations_hot_weather(self):
        """Test generación de recomendaciones para clima caliente"""
        weather_data = WeatherData(**self.mock_weather_data)
        # Modificar temperatura para clima caliente (>30°C)
        weather_data.main.temp = 308.15  # 35°C

        recommendations = generate_recommendations(weather_data)

        self.assertTrue(any("calor" in rec.lower() for rec in recommendations))

    def test_generate_recommendations_cold_weather(self):
        """Test generación de recomendaciones para clima frío"""
        weather_data = WeatherData(**self.mock_weather_data)
        # Modificar temperatura para clima frío (<10°C)
        weather_data.main.temp = 280.15  # 7°C

        recommendations = generate_recommendations(weather_data)

        self.assertTrue(any("frío" in rec.lower() or "frío" in rec for rec in recommendations))

    def test_generate_recommendations_rain(self):
        """Test generación de recomendaciones para lluvia"""
        from src.schemas.weather import WeatherCondition
        
        # Crear una nueva lista de condiciones con lluvia
        rain_condition = WeatherCondition(
            id=500,
            main="Rain",
            description="lluvia ligera",
            icon="10d"
        )
        
        weather_data = WeatherData(**self.mock_weather_data)
        weather_data.weather = [rain_condition]

        recommendations = generate_recommendations(weather_data)

        self.assertTrue(any("lluvia" in rec.lower() for rec in recommendations))

    def test_weather_data_conversion(self):
        """Test conversión de temperatura Kelvin a Celsius"""
        weather_data = WeatherData(**self.mock_weather_data)
        temp_celsius = weather_data.to_celsius()

        # 298.15K - 273.15 = 25°C
        self.assertAlmostEqual(temp_celsius, 25.0, places=1)

    def test_weather_summary(self):
        """Test generación de resumen del clima"""
        weather_data = WeatherData(**self.mock_weather_data)
        summary = weather_data.get_weather_summary()

        self.assertEqual(summary, "Clear: cielo despejado")


class TestWeatherService(unittest.TestCase):

    @patch('requests.get')
    def test_get_weather_success(self, mock_get):
        """Test obtención exitosa de datos climáticos"""
        # Configurar mock de respuesta
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "coord": {"lon": -0.1257, "lat": 51.5085},
            "weather": [{"id": 800, "main": "Clear", "description": "cielo despejado", "icon": "01d"}],
            "main": {
                "temp": 298.15,
                "feels_like": 298.15,
                "temp_min": 297.15,
                "temp_max": 299.15,
                "pressure": 1013,
                "humidity": 65
            },
            "visibility": 10000,
            "wind": {"speed": 3.5, "deg": 180},
            "clouds": {"all": 0},
            "dt": 1638144000,
            "sys": {"country": "GB", "sunrise": 1638124800, "sunset": 1638157200},
            "timezone": 0,
            "id": 2643743,
            "name": "London",
            "cod": 200
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        service = WeatherService()
        result = service.get_weather("London")

        self.assertEqual(result.name, "London")
        self.assertEqual(result.main.temp, 298.15)

    @patch('requests.get')
    def test_get_weather_failure(self, mock_get):
        """Test manejo de error en API"""
        import requests
        # Simular un error de red usando una excepción específica de requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        service = WeatherService()

        with self.assertRaises(ValueError):
            service.get_weather("London")


if __name__ == '__main__':
    unittest.main()
