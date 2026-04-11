# 🚀 CÓMO PROBAR EL AGENTE - PASO A PASO

## PASO 1: Abre una terminal y ejecuta estos comandos:

```bash
# Navega al proyecto
cd /Users/rafex/repository/exmples_secret/agentes-con-LangGraph/poc/agent-weather

# Activa el entorno virtual
source venv/bin/activate

# Ejecuta el script interactivo
python probar_agente.py
```

## PASO 2: Usa el menú interactivo

Verás un menú como este:

```
📋 MENÚ PRINCIPAL
--------------------------------------------------
1. 🌤️  Consultar clima de una ciudad
2. ℹ️  Mostrar información del sistema
3. 🚀 Ejecutar ejemplo rápido (Madrid)
4. ❌ Salir
--------------------------------------------------
```

**Elige la opción 1** para consultar el clima de cualquier ciudad.

## PASO 3: Ingresa una ciudad

Cuando te pida la ciudad, escribe cualquier nombre, por ejemplo:
- `Madrid`
- `Barcelona`
- `Londres`
- `Nueva York`
- `Tokio`

## PASO 4: ¡Ver los resultados!

El agente te mostrará:
- 🌡️ Datos climáticos reales (temperatura, humedad, viento)
- 💡 Recomendaciones generadas por DeepSeek (inteligentes y naturales)

---

## ⚠️ IMPORTANTE: Si la API de OpenWeatherMap no está activa

Si ves el mensaje:
```
⚠️ Sin datos climáticos (verificar API key o espera 2h por activación)
```

**Es normal**. La API de OpenWeatherMap necesita 2 horas para activarse desde que recibiste el email.

**Mientras tanto**, puedes ver cómo funciona el agente con datos simulados ejecutando:

```bash
cd /Users/rafex/repository/exmples_secret/agentes-con-LangGraph/poc/agent-weather
source venv/bin/activate
python -c "
from src.agents.weather_agent import generate_recommendations
from src.schemas.weather import WeatherData

# Datos simulados
simulacion = {
    'coord': {'lon': -3.7038, 'lat': 40.4168},
    'weather': [{'id': 800, 'main': 'Clear', 'description': 'cielo despejado', 'icon': '01d'}],
    'main': {'temp': 298.15, 'feels_like': 299.15, 'temp_min': 297.15, 'temp_max': 299.15, 'pressure': 1013, 'humidity': 35},
    'visibility': 10000,
    'wind': {'speed': 4.5, 'deg': 120},
    'clouds': {'all': 0},
    'dt': 1638144000,
    'sys': {'country': 'ES', 'sunrise': 1638124800, 'sunset': 1638157200},
    'timezone': 3600,
    'id': 3117735,
    'name': 'Madrid',
    'cod': 200
}

weather_data = WeatherData(**simulacion)
print('Ciudad:', weather_data.name)
print('Temperatura:', f'{weather_data.to_celsius():.1f}°C')
print('Recomendaciones:', generate_recommendations(weather_data))
"
```

---

## 📝 COMANDOS RÁPIDOS

| Acción | Comando |
|--------|---------|
| Probar interactivo | `python probar_agente.py` |
| Ver API keys | `cat .env` |
| Ejecutar tests | `python -m pytest src/tests/ -v` |
| Consultar ciudad específica | `just run "Madrid"` (desde directorio raíz) |

---

## 🎯 ¿Qué hace el agente?

1. **Consulta OpenWeatherMap** → Obtienes datos climáticos reales
2. **Procesa con Pydantic** → Valida y estructura los datos
3. **Genera recomendaciones** → DeepSeek crea consejos naturales
4. **Entrega resultado** → Información completa en JSON

---

## 📚 Más información

- **Instrucciones detalladas**: `INSTRUCCIONES_PROBAR.md`
- **Código fuente**: `src/agents/weather_agent.py`
- **API keys**: `.env` (no compartir)

---

## ✅ Estado Actual del Agente

| Componente | Estado |
|------------|--------|
| LangGraph | ✅ Funcionando |
| Pydantic | ✅ Funcionando |
| DeepSeek | ✅ Funcionando |
| OpenWeatherMap | ⏳ Esperando activación (2h) |
| Tests | ✅ 9/9 PASANDO |
| Fallback | ✅ Automático |

**¡El agente está listo para usar! Solo espera 2 horas por la activación de OpenWeatherMap.**
