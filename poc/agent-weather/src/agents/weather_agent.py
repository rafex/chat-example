from typing import TypedDict, Annotated, Sequence, Optional
from langgraph.graph import StateGraph, END, START
from src.services.weather_service import WeatherService
from src.services.deepseek_service import DeepSeekService
from src.schemas.weather import WeatherData, AnalysisResult
from datetime import datetime

# Definir el estado del agente
class AgentState(TypedDict):
    location: str
    weather_data: Optional[WeatherData]
    analysis: Optional[AnalysisResult]
    recommendations: Sequence[str]
    error: Optional[str]

def fetch_weather(state: AgentState) -> AgentState:
    """Nodo: Obtener datos climáticos de la API"""
    try:
        weather_service = WeatherService()
        weather_data = weather_service.get_weather(state["location"])
        return {**state, "weather_data": weather_data}
    except Exception as e:
        print(f"Error obteniendo datos climáticos: {e}")
        # Agregamos el error al estado para que pueda ser manejado downstream
        return {**state, "weather_data": None, "error": str(e)}

def analyze_weather(state: AgentState) -> AgentState:
    """Nodo: Analizar datos climáticos y generar recomendaciones con DeepSeek"""
    weather_data = state.get("weather_data")
    if not weather_data:
        return {**state, "analysis": None, "recommendations": ["No se pudieron obtener datos climáticos"]}

    # Convertir temperatura a Celsius
    temp_celsius = weather_data.to_celsius()
    condition = weather_data.get_weather_summary()

    # Preparar datos para DeepSeek
    weather_info = {
        "location": weather_data.name,
        "temperature_celsius": temp_celsius,
        "condition": condition,
        "humidity": weather_data.main.humidity,
        "wind_speed": weather_data.wind.speed
    }

    # Generar recomendaciones usando DeepSeek
    try:
        deepseek_service = DeepSeekService()
        llm_recommendations = deepseek_service.generate_recommendations(weather_info)
        recommendations = [llm_recommendations]
    except Exception as e:
        print(f"Error con DeepSeek, usando recomendaciones básicas: {e}")
        # Fallback a recomendaciones básicas si DeepSeek falla
        recommendations = generate_recommendations(weather_data)

    analysis = AnalysisResult(
        location=weather_data.name,
        temperature=weather_data.main.temp,
        temperature_celsius=temp_celsius,
        condition=condition,
        humidity=weather_data.main.humidity,
        wind_speed=weather_data.wind.speed,
        recommendations=recommendations,
        timestamp=datetime.now()
    )

    return {**state, "analysis": analysis, "recommendations": recommendations}

def generate_recommendations(weather_data: WeatherData) -> list[str]:
    """Genera recomendaciones basadas en las condiciones climáticas"""
    recommendations = []

    # Análisis de temperatura
    temp_celsius = weather_data.to_celsius()
    if temp_celsius > 30:
        recommendations.append("🥵 Hace calor: Usa ropa ligera, bebe agua y evita la exposición solar directa")
    elif temp_celsius < 10:
        recommendations.append("🥶 Hace frío: Abrígate bien, usa capas de ropa y evita cambios bruscos de temperatura")

    # Análisis de humedad
    humidity = weather_data.main.humidity
    if humidity > 80:
        recommendations.append("💧 Alta humedad: Considera llevar ropa transpirable y protector solar")
    elif humidity < 30:
        recommendations.append("🏜️ Baja humedad: Hidratación importante, usa humectante para la piel")

    # Análisis de viento
    wind_speed = weather_data.wind.speed
    if wind_speed > 10:
        recommendations.append("💨 Viento fuerte: Ten cuidado con objetos sueltos, usa ropa que no vuele")

    # Análisis de condiciones (soporta inglés y español)
    for condition in weather_data.weather:
        desc = condition.description.lower()
        if "rain" in desc or "lluvia" in desc:
            recommendations.append("🌧️ Lluvia esperada: Lleva paraguas o impermeable")
        elif "snow" in desc or "nieve" in desc:
            recommendations.append("❄️ Nieve esperada: Usa calzado antideslizante y abrígate")
        elif "clear" in desc or "despejado" in desc:
            recommendations.append("☀️ Cielo despejado: Excelente día para actividades al aire libre")

    if not recommendations:
        recommendations.append("✅ Condiciones climáticas normales para esta época del año")

    return recommendations

# Construir el grafo LangGraph
builder = StateGraph(AgentState)

builder.add_node("fetch", fetch_weather)
builder.add_node("analyze", analyze_weather)

builder.add_edge(START, "fetch")
builder.add_edge("fetch", "analyze")
builder.add_edge("analyze", END)

graph = builder.compile()

def run_weather_agent(location: str) -> dict:
    """Función principal para ejecutar el agente"""
    initial_state = {
        "location": location,
        "weather_data": None,
        "analysis": None,
        "recommendations": []
    }

    try:
        result = graph.invoke(initial_state)

        return {
            "success": True,
            "location": result["location"],
            "weather_data": result["weather_data"].model_dump() if result["weather_data"] else None,
            "analysis": result["analysis"].model_dump() if result["analysis"] else None,
            "recommendations": result["recommendations"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "location": location
        }
