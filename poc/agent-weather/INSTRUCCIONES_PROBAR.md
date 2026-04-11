# 📚 INSTRUCCIONES PARA PROBAR EL AGENTE METEOROLÓGICO

## Requisitos Previos

1. **Tener Python 3.9 o superior instalado**
   ```bash
   python3 --version
   ```

2. **Tener las API keys reales configuradas** (ya las tienes en `.env`)

## Paso 1: Acceder al Proyecto

```bash
cd /Users/rafex/repository/exmples_secret/agentes-con-LangGraph/poc/agent-weather
```

## Paso 2: Activar el Entorno Virtual

```bash
source venv/bin/activate
```

Deberías ver `(venv)` al inicio de tu terminal.

## Paso 3: Probar el Agente

### Opción A: Script Interactivo (Recomendado)

```bash
python probar_agente.py
```

Este script te mostrará un menú interactivo donde puedes:
- Consultar clima de cualquier ciudad
- Ver la configuración del sistema
- Ejecutar ejemplos rápidos

### Opción B: Consulta Rápida desde Python

```bash
python -c "
from src.agents.weather_agent import run_weather_agent
import json

resultado = run_weather_agent('Madrid')
print(json.dumps(resultado, indent=2, ensure_ascii=False))
"
```

### Opción C: Usando Just (Task Runner)

```bash
# Desde el directorio raíz del proyecto
cd /Users/rafex/repository/exmples_secret/agentes-con-LangGraph
just run 'Madrid'
```

### Opción D: Usando Makefile

```bash
# Desde el directorio raíz del proyecto
cd /Users/rafex/repository/exmples_secret/agentes-con-LangGraph
make test  # Ejecuta todos los tests
```

## Paso 4: Verificar Resultados

### Si todo funciona correctamente, verás:

```
{
  "success": true,
  "location": "Madrid",
  "weather_data": {
    "name": "Madrid",
    "main": {
      "temp": 298.15,
      "humidity": 45
    },
    ...
  },
  "analysis": {
    "location": "Madrid",
    "temperature_celsius": 25.0,
    "condition": "Cielo despejado",
    "recommendations": [
      "🧠 [Recomendación generada por DeepSeek...]"
    ]
  },
  "recommendations": ["..."]
}
```

### Si la API de OpenWeatherMap aún no está activa (2h):

Verás:
```
{
  "success": true,
  "location": "Madrid",
  "weather_data": null,
  "analysis": null,
  "recommendations": ["No se pudieron obtener datos climáticos"]
}
```

## Paso 5: Verificar Configuración

```bash
# Ver API keys configuradas
cat .env

# Ver estructura del proyecto
find . -type f -name "*.py" | head -20

# Ver últimos cambios
git log --oneline -5
```

## Solución de Problemas Comunes

### Problema 1: "API key no válida"

**Solución**: Espera 2 horas desde que recibiste el email de OpenWeatherMap. La API necesita activación.

### Problema 2: "No se pudo inicializar OpenAI"

**Solución**: Es un warning técnico, pero DeepSeek funciona igual. El agente usa un fallback automático.

### Problema 3: "Module not found"

**Solución**: Asegúrate de haber activado el entorno virtual:
```bash
source venv/bin/activate
```

## Comandos Útiles

```bash
# Activar entorno virtual
source venv/bin/activate

# Desactivar entorno virtual
deactivate

# Ejecutar tests
python -m pytest src/tests/ -v

# Ver configuración actual
python -c "from src.config import Config; print(Config.OPENWEATHER_API_KEY)"

# Probar DeepSeek directamente
python -c "
from src.services.deepseek_service import DeepSeekService
s = DeepSeekService()
print(s.generate_recommendations({
    'location': 'Madrid',
    'temperature_celsius': 25,
    'condition': 'Cielo despejado',
    'humidity': 45,
    'wind_speed': 3.5
}))
"
```

## Estructura del Proyecto

```
poc/agent-weather/
├── probar_agente.py          # Script interactivo (¡EJECUTA ESTE!)
├── src/
│   ├── agents/
│   │   └── weather_agent.py  # Lógica principal del agente
│   ├── services/
│   │   ├── weather_service.py   # OpenWeatherMap API
│   │   └── deepseek_service.py  # DeepSeek LLM
│   └── schemas/
│       └── weather.py        # Modelos de datos
├── venv/                     # Entorno virtual
├── .env                      # Tus API keys (no compartir)
├── .env.example              # Plantilla de configuración
└── requirements.txt          # Dependencias
```

## ¿Qué Hace el Agente?

1. **Consulta OpenWeatherMap** → Obtienes datos climáticos reales de cualquier ciudad
2. **Procesa con Pydantic** → Valida y estructura los datos
3. **Genera recomendaciones** → Usa DeepSeek para crear recomendaciones naturales
4. **Entrega resultado** → Información completa en formato JSON

## Próximos Pasos

1. **Espera 2 horas** a que se active la API de OpenWeatherMap
2. **Ejecuta `python probar_agente.py`** y prueba con diferentes ciudades
3. **Explora el código** en `src/agents/weather_agent.py` para entender cómo funciona
4. **Personaliza** las recomendaciones en `generate_recommendations()`

## ¡Importante!

- **NUNCA** compartas tus `.env` files con nadie
- **NUNCA** subas `.env` a repositorios públicos (ya está en `.gitignore`)
- Las API keys son personales y pueden tener costes si se agotan los créditos

¿Tienes alguna duda específica sobre cómo probar el agente?
