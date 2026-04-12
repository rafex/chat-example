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

1.  **Instalar Python 3.14**: Asegúrate de tener Python 3.14 o superior instalado en tu sistema.
    ```bash
    # Ejemplo de instalación en macOS con Homebrew
    brew install python@3.14
    ```
2.  **Entorno Virtual**: Crea y activa un entorno virtual para aislar las dependencias del proyecto.
    ```bash
    python3.14 -m venv venv
    source venv/bin/activate
    ```
3.  **Instalar Dependencias**: Instala las dependencias del proyecto.
    ```bash
    make install
    # o
    just install
    ```
4.  **Variables de Entorno**: Copia la plantilla y configura tus claves de API en `poc/.env`.
    ```bash
    cp poc/.env.example poc/.env
    ```
    Configura las siguientes variables en `poc/.env`:
    - `OPENWEATHER_API_KEY`: Tu clave de API de OpenWeatherMap.
    - `OPENAI_API_KEY`, `DEEPSEEK_API_KEY`, `OPENROUTER_API_KEY`: Claves para los LLMs (según el proveedor seleccionado).
    - `CURRENT_LLM_PROVIDER`: Define el LLM por defecto (`deepseek`, `openai`, `openrouter`).
5.  **Logger Estructurado**: La configuración del logger está integrada y lista para usarse. Los logs se generarán automáticamente en un formato estructurado para facilitar el análisis y la depuración.


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

### Ejemplos de Uso

El `chatCLI` integrado permite interactuar directamente con el agente orquestador.

**Escenarios comunes:**

1.  **Consulta de Clima**:
    ```
    Usuario: "¿Cómo está el clima en Madrid?"
    Asistente: El agente orquestador detecta la intención, utiliza la herramienta `weather.get_current_weather` y proporciona el pronóstico actual.
    ```
2.  **Uso de Herramientas MCP**:
    ```
    Usuario: "say_hello(name=Juan, lang=es)"
    Asistente: El orquestador identifica la llamada a una herramienta MCP y ejecuta `mcp.say_hello`, respondiendo "Hola Juan".
    ```
3.  **Interacción Conversacional y Memoria**:
    ```
    Usuario: "hola, me llamo Carlos y vivo en Barcelona"
    Asistente: El sistema registra esta información en la memoria conversacional y semántica.
    Usuario: "¿Cuál es la capital de España?"
    Asistente: El agente utiliza su conocimiento general o la memoria para responder "Madrid".
    ```
4.  **Cambio de LLM**:
    ```
    Usuario: "/model openai"
    Asistente: El `chatCLI` actualiza la configuración para usar el modelo de OpenAI.
    ```
5.  **Comandos del Chat CLI**:
    - `/model [openai|deepseek|openrouter]`: Cambiar proveedor LLM.
    - `mcp list-tools`: Listar herramientas MCP disponibles.
    - `historial`: Ver historial de la sesión.
    - `herramientas`: Ver todas las herramientas registradas y disponibles.
    - `limpiar`: Limpiar la pantalla.
    - `ayuda`: Mostrar todos los comandos disponibles.
    - `salir`: Terminar la conversación.


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

- **LangGraph 1.1.6**: Orquestación avanzada de grafos de estado para la toma de decisiones del agente.
- **Python 3.14**: Entorno de ejecución recomendado.
- **Arquitectura de Orquestación**:
    - **ToolRegistry**: Registro centralizado y determinista de todas las herramientas disponibles.
    - **DecisionValidator**: Valida rigurosamente las decisiones del LLM antes de la ejecución.
- **Memoria Semántica y Conversacional**:
    - **FAISS**: Indexación y recuperación de contexto a largo plazo mediante embeddings.
    - **Memoria Conversacional**: Mantiene el historial reciente para la continuidad del diálogo.
- **Logger Estructurado**: Para una observabilidad detallada del flujo del agente y las interacciones.
- **chatCLI Integrado**: Interfaz de línea de comandos que interactúa directamente con el agente orquestador.
- **Soporte Multi-LLM**: Configurable para usar DeepSeek, OpenAI, u OpenRouter.
- **Configuración TOML**: Prompts del agente orquestador y configuraciones de herramientas vía `prompts.toml`.
- **Agente Meteorológico**: Consulta la API de OpenWeatherMap y genera recomendaciones con LLM.
- **MCP Router**: Integra herramientas adicionales (saludos multilingües, etc.).

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
