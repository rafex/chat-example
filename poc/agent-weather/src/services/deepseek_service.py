import json
import sys
import os
from typing import List, Dict, Optional

# Asegurar que el directorio padre de 'src' esté en el path para importar config
current_dir = os.path.dirname(os.path.abspath(__file__))
agent_weather_src = os.path.dirname(current_dir)  # poc/agent-weather/src
agent_weather_root = os.path.dirname(agent_weather_src)  # poc/agent-weather

if agent_weather_root not in sys.path:
    sys.path.insert(0, agent_weather_root)

try:
    from src.config import Config
except ImportError:
    # Fallback: intentar importar directamente si 'src' no está como paquete
    try:
        sys.path.insert(0, agent_weather_src)
        from config import Config
    except ImportError:
        raise ImportError("No se pudo importar Config desde src.config ni config")

class LLMProviderService:
    """Servicio para interactuar con proveedores LLM genéricos (compatible con OpenAI)"""

    def __init__(self):
        # Obtener API key usando métodos de Config (con fallback a variables antiguas)
        api_key = Config.get_llm_api_key()
        if not api_key:
            raise ValueError("LLM_PROVIDER_API_KEY no está configurada en variables de entorno")

        # Obtener configuración del LLM
        api_base = Config.get_llm_api_base()
        model = Config.get_llm_model()

        try:
            import os
            from openai import OpenAI
            
            # Establecer API key en variable de entorno para evitar problemas con httpx
            original_api_key = os.environ.get('OPENAI_API_KEY')
            os.environ['OPENAI_API_KEY'] = api_key
            
            # Limpiar variables de proxy que puedan causar problemas
            original_proxies = {}
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']
            for var in proxy_vars:
                if var in os.environ:
                    original_proxies[var] = os.environ[var]
                    del os.environ[var]
            
            try:
                # Intentar crear cliente
                self.client = OpenAI(
                    api_key=api_key,
                    base_url=api_base,
                )
                self.model = model
                self.available = True
                print(f"✅ LLM Provider configurado: {api_base} (model: {model})")
            except TypeError as te:
                if "proxies" in str(te):
                    # Solución alternativa: usar httpx directamente
                    print(f"⚠️  Usando workaround para proxy...")
                    import httpx
                    
                    # Crear cliente httpx sin proxy
                    http_client = httpx.Client(proxy=None)
                    
                    self.client = OpenAI(
                        api_key=api_key,
                        base_url=api_base,
                        http_client=http_client
                    )
                    self.model = model
                    self.available = True
                    print(f"✅ LLM Provider configurado con workaround: {api_base} (model: {model})")
                else:
                    raise
            finally:
                # Restaurar variables originales
                if original_api_key is not None:
                    os.environ['OPENAI_API_KEY'] = original_api_key
                elif 'OPENAI_API_KEY' in os.environ:
                    del os.environ['OPENAI_API_KEY']
                
                for var, value in original_proxies.items():
                    os.environ[var] = value
                    
        except Exception as e:
            print(f"⚠️ No se pudo inicializar LLM Provider: {e}")
            import traceback
            traceback.print_exc()
            self.available = False

    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        """
        Realiza una conversación con el LLM usando formato OpenAI.

        Args:
            messages: Lista de mensajes en formato OpenAI
            model: Modelo a usar (por defecto el configurado)

        Returns:
            str: Respuesta del modelo
        """
        if not self.available:
            return "El servicio LLM no está disponible."

        if model is None:
            model = self.model

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )

            return response.choices[0].message.content.strip() if response.choices and response.choices[0].message.content else ""

        except Exception as e:
            print(f"Error en chat con LLM: {e}")
            return ""

    def generate_recommendations(self, weather_data: dict) -> str:
        """
        Genera recomendaciones meteorológicas usando el LLM.

        Args:
            weather_data: Diccionario con datos del clima

        Returns:
            str: Recomendaciones generadas por el LLM
        """
        if not self.available:
            return self.fallback_recommendations(weather_data)

        # Preparar el prompt con datos del clima
        temp_celsius = weather_data.get("temperature_celsius", 0)
        condition = weather_data.get("condition", "")
        humidity = weather_data.get("humidity", 0)
        wind_speed = weather_data.get("wind_speed", 0)
        location = weather_data.get("location", "")

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
            response = self.client.chat.completions.create(
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
            print(f"Error con LLM API: {e}")
            return self.fallback_recommendations(weather_data)

    def fallback_recommendations(self, weather_data: dict) -> str:
        """Recomendaciones básicas si el LLM falla"""
        temp_celsius = weather_data.get("temperature_celsius", 0)
        humidity = weather_data.get("humidity", 0)
        wind_speed = weather_data.get("wind_speed", 0)
        condition = weather_data.get("condition", "")

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


# Backward compatibility: alias para el nombre antiguo
DeepSeekService = LLMProviderService
