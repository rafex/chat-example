# Sistema de Agentes con LangGraph

Sistema multi-agente inteligente que integra **OpenWeatherMap** para clima, **MCP** para herramientas adicionales y **LLM** (DeepSeek/OpenAI/OpenRouter) para análisis de intención y conversación.

## Características

- **Agente Orquestador**: Decide qué herramienta usar basándose en la intención del usuario
- **Agente Meteorológico**: Consulta la API de OpenWeatherMap y genera recomendaciones con LLM
- **MCP Router**: Integra herramientas adicionales (saludos multilingües, etc.)
- **Memoria FAISS**: Contexto de conversación con embeddings semánticos
- **Soporte Multi-LLM**: DeepSeek, OpenAI y OpenRouter configurables dinámicamente
- **Configuración TOML**: Prompts del agente orquestador configurables vía archivo TOML

## Estructura del Proyecto

```
.
├── Makefile                    # Build system
├── Justfile                    # Task runner
├── README.md                   # Documentación
├── poc/                        # Directorio de pruebas y proyectos
│   ├── .env                    # Variables de entorno compartidas
│   ├── .env.example            # Plantilla de variables de entorno
│   ├── agent-weather/          # Agente meteorológico
│   │   ├── src/                # Código fuente
│   │   ├── venv/               # Entorno virtual
│   │   └── requirements.txt    # Dependencias Python
│   ├── agent-orquestador/      # Agente orquestador
│   │   ├── src/                # Código fuente
│   │   └── config/             # Configuración (prompts.toml)
│   └── chatCLI/                # Chat CLI (interfaz de entrada/salida)
│       ├── src/                # Código fuente
│       └── venv/               # Entorno virtual
└── lib/mcp/                    # MCP Router (herramientas adicionales)
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
cp poc/.env.example poc/.env
```

2. Configura las API Keys en `poc/.env`:
   - `OPENWEATHER_API_KEY`: Clave de OpenWeatherMap (obtenla en https://openweathermap.org/api)
   - `OPENAI_API_KEY`: Clave de OpenAI (opcional)
   - `DEEPSEEK_API_KEY`: Clave de DeepSeek (opcional)
   - `OPENROUTER_API_KEY`: Clave de OpenRouter (opcional)

3. Configura el proveedor LLM por defecto:
   ```bash
   # En poc/.env
   CURRENT_LLM_PROVIDER=deepseek  # deepseek, openai, o openrouter
   ```

### Ejecutar el Chat CLI

```bash
cd poc/chatCLI
source venv/bin/activate
python src/chat_cli.py
```

### Comandos disponibles en el Chat CLI

- `/model [openai|deepseek|openrouter]`: Cambiar proveedor LLM
- `mcp list-tools`: Listar herramientas MCP disponibles
- `historial`: Ver historial de la sesión
- `herramientas`: Ver herramientas disponibles
- `limpiar`: Limpiar pantalla
- `ayuda`: Mostrar todos los comandos
- `salir`: Terminar la conversación

### Ejemplos de uso

```
Usuario: "¿Cómo está el clima en Madrid?"
Asistente: Consulta el clima de Madrid y genera recomendaciones

Usuario: "say_hello(name=Juan, lang=es)"
Asistente: Saluda a Juan en español

Usuario: "/model openai"
Asistente: Cambia a proveedor OpenAI

Usuario: "hola, me llamo Carlos y vivo en Barcelona"
Asistente: Recuerda el nombre y ubicación del usuario
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
- **DeepSeek**: LLM open source para generación de recomendaciones conversacionales
- **Pydantic**: Validación y modelos de datos
- **Requests**: Cliente HTTP para OpenWeatherMap
- **Python-dotenv**: Gestión de variables de entorno
- **pytest**: Framework de pruebas
- **OpenAI SDK**: Cliente para APIs compatibles (usado con DeepSeek)

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
