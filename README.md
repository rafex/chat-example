# Agente Meteorológico con LangGraph

Un agente inteligente que consume la API de OpenWeatherMap para proporcionar información climática y recomendaciones personalizadas.

## Características

- **Consumo de API**: Cliente HTTP para la API pública de OpenWeatherMap
- **Análisis de clima**: Procesamiento de datos meteorológicos (temperatura, humedad, viento)
- **Recomendaciones**: Generación de consejos basados en condiciones climáticas
- **Flujo LangGraph**: Orquestación del agente usando grafos de estado

## Estructura del Proyecto

```
.
├── Makefile               # Build system
├── Justfile              # Task runner
├── README.md             # Documentación
└── poc/agent-weather/    # Directorio del proyecto
    ├── src/              # Código fuente
    │   ├── agents/       # Lógica del agente LangGraph
    │   ├── services/     # Cliente HTTP para OpenWeatherMap
    │   ├── schemas/      # Modelos Pydantic
    │   ├── config.py     # Configuración
    │   └── tests/        # Pruebas unitarias
    ├── venv/             # Entorno virtual
    ├── requirements.txt  # Dependencias Python
    ├── .env              # Variables de entorno (API Key) - Ignorado en git
    └── .env.example      # Plantilla de variables de entorno
```

## Uso

### Instalación

```bash
# Instalar dependencias
make install

# O usando Just
just install
```

### Configuración

1. Copia la plantilla de variables de entorno:
```bash
cp poc/agent-weather/.env.example poc/agent-weather/.env
```

2. Edita `poc/agent-weather/.env` con tu API Key de OpenWeatherMap:
```bash
OPENWEATHER_API_KEY=tu_api_key_aqui
```

### Ejecución

**Usando Makefile:**
```bash
make test          # Ejecutar pruebas
make lint          # Verificar código
make format        # Formatear código
```

**Usando Justfile:**
```bash
just test           # Ejecutar pruebas
just run "Madrid"   # Consultar clima de Madrid
just lint           # Verificar código
just format         # Formatear código
```

**Directamente con Python:**
```bash
cd poc/agent-weather
source venv/bin/activate
python3 -c "from src.agents.weather_agent import run_weather_agent; print(run_weather_agent('Madrid'))"
```

## Tecnologías

- **LangGraph**: Orquestación de grafos de estado para el agente
- **Pydantic**: Validación y modelos de datos
- **Requests**: Cliente HTTP
- **Python-dotenv**: Gestión de variables de entorno
- **pytest**: Framework de pruebas

## Tests

Ejecutar suite de pruebas:

```bash
# Con cobertura
just test-cov

# Pruebas específicas
cd poc/agent-weather
source venv/bin/activate
python3 -m pytest src/tests/test_weather_agent.py::TestWeatherAgent::test_generate_recommendations_rain -v
```

## API de OpenWeatherMap

El agente consume la API pública de OpenWeatherMap:
- Endpoint: `https://api.openweathermap.org/data/2.5/weather`
- Límite gratuito: 1000 llamadas/día
- Idioma: Español (`lang=es`)

## Licencia

MIT License
