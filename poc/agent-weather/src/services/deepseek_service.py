import json
from src.config import Config

class DeepSeekService:
    """Servicio para interactuar con DeepSeek API (compatible con formato OpenAI)"""

    def __init__(self):
        if not Config.DEEPSEEK_API_KEY:
            raise ValueError("DEEPSEEK_API_KEY no está configurada en variables de entorno")
        
        # Algunas instalaciones pueden requerir estos parámetros
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=Config.DEEPSEEK_API_KEY,
                base_url=Config.DEEPSEEK_API_BASE
            )
            self.model = Config.DEEPSEEK_MODEL
            self.available = True
        except Exception as e:
            print(f"⚠️ No se pudo inicializar OpenAI: {e}")
            self.available = False

    def generate_recommendations(self, weather_data: dict) -> str:
        """
        Genera recomendaciones meteorológicas usando DeepSeek.
        
        Args:
            weather_data: Diccionario con datos del clima
            
        Returns:
            str: Recomendaciones generadas por el LLM
        """
        if not self.available:
            return self.fallback_recommendations(weather_data)

        # Preparar el prompt con datos del clima
        temp_celsius = weather_data["temperature_celsius"]
        condition = weather_data["condition"]
        humidity = weather_data["humidity"]
        wind_speed = weather_data["wind_speed"]
        location = weather_data["location"]

        prompt = f"""Eres un asistente meteorológico experto. Genera recomendaciones útiles y naturales
basadas en las siguientes condiciones climáticas para {location}:

Temperatura: {temp_celsius:.1f}°C
Condición: {condition}
Humedad: {humidity}%
Velocidad del viento: {wind_speed} m/s

Instrucciones:
- Sé conciso y práctico (máximo 100 palabras)
- Incluye emojis para hacerlo más amigable
- Da recomendaciones específicas basadas en los datos
- Si el clima es normal, indica que es un día normal
- Responde en español

Recomendaciones:
"""

        try:
            # Intentar con la librería openai
            from openai import OpenAI
            client = OpenAI(
                api_key=Config.DEEPSEEK_API_KEY,
                base_url=Config.DEEPSEEK_API_BASE
            )
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un asistente meteorológico experto que da recomendaciones prácticas y útiles."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )

            return response.choices[0].message.content.strip() if response.choices and response.choices[0].message.content else self.fallback_recommendations(weather_data)

        except Exception as e:
            print(f"Error con DeepSeek API: {e}")
            return self.fallback_recommendations(weather_data)

    def fallback_recommendations(self, weather_data: dict) -> str:
        """Recomendaciones básicas si el LLM falla"""
        temp_celsius = weather_data["temperature_celsius"]
        humidity = weather_data["humidity"]
        wind_speed = weather_data["wind_speed"]
        condition = weather_data["condition"]

        recommendations = []
        
        if temp_celsius > 30:
            recommendations.append("🥵 Hace calor: Usa ropa ligera, bebe agua")
        elif temp_celsius < 10:
            recommendations.append("🥶 Hace frío: Abrígate bien, usa capas")
        
        if humidity > 80:
            recommendations.append("💧 Alta humedad: Ropa transpirable")
        elif humidity < 30:
            recommendations.append("🏜️ Baja humedad: Hidratación importante")
        
        if wind_speed > 10:
            recommendations.append("💨 Viento fuerte: Ten cuidado")
        
        desc = condition.lower()
        if "lluvia" in desc or "rain" in desc:
            recommendations.append("🌧️ Lluvia: Lleva paraguas")
        elif "nieve" in desc or "snow" in desc:
            recommendations.append("❄️ Nieve: Calzado antideslizante")
        
        if not recommendations:
            recommendations.append("✅ Clima normal para hoy")

        return " ".join(recommendations)
