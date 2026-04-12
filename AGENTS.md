# AGENTS.md - Información para Agentes de IA

## Visión General del Proyecto

Este proyecto es una **Proof of Concept (POC)** que demuestra el uso de **LangGraph** para crear un sistema de agentes inteligentes con las siguientes características:

### Objetivos Principales

1. **Chat Interface**: Interfaz de entrada/salida de texto con memoria FAISS
2. **Agente Orquestador**: Coordina el uso de herramientas disponibles
3. **Herramientas Específicas**: Agentes especializados (clima, MCP)
4. **No Inventar Herramientas**: El agente orquestador solo usa herramientas que realmente existen
5. **LangGraph**: Implementación de agentes usando grafos de estado

## Arquitectura del Sistema

### Flujo de Ejecución

```
Usuario → Chat CLI → Agente Orquestador (LangGraph) → [Herramientas disponibles]
                                     ↓
                              LLM (DeepSeek/OpenAI/OpenRouter)
                                     ↓
                              Análisis de Intención
                                     ↓
                              Decisión de Herramienta
                                     ↓
                              Ejecución → Resultado → Memoria FAISS
```

### Componentes Clave

1. **Chat CLI** (`poc/chatCLI/`)
   - Interfaz de entrada/salida de texto
   - Gestión de memoria FAISS (embeddings semánticos)
   - Comunicación con agente orquestador
   - **NO tiene lógica de inferencia propia**

2. **Agente Orquestador** (`poc/agent-orquestador/`)
   - Usa LangGraph para orquestar flujos de ejecución
   - Analiza intención del usuario usando LLM
   - Decide qué herramienta usar basándose en análisis
   - **NO inventa herramientas** - solo usa las disponibles
   - Configuración de prompts en TOML (`config/prompts.toml`)

3. **Herramientas Específicas**
   - **Agente Meteorológico** (`poc/agent-weather/`): Consulta OpenWeatherMap
   - **MCP Router** (`lib/mcp/`): Herramientas adicionales (saludos multilingües, etc.)

4. **Memoria FAISS**
   - Almacena contexto de conversación
   - Usa embeddings semánticos (all-MiniLM-L6-v2)
   - Recupera contexto relevante para cada interacción

## Flujo de Trabajo Detallado

### 1. Análisis de Intención (LLM)

El agente orquestador envía al LLM:
- **Sistema**: Instrucciones con herramientas disponibles
- **Historial**: Conversaciones recientes
- **Usuario**: Mensaje actual

El LLM responde con JSON:
```json
{
  "intent": "weather_query",
  "tool_type": "weather",
  "tool_name": "say_hello",  // solo si tool_type es "mcp"
  "arguments": {"location": "Madrid"},
  "confidence": 0.95
}
```

### 2. Decisión de Herramienta

Basado en el análisis, el orquestador:
- Si `tool_type == "weather"` → Ejecuta agente meteorológico
- Si `tool_type == "mcp"` → Ejecuta herramienta MCP específica
- Si `tool_type == "chat"` → Usa conversación genérica

### 3. Ejecución y Memoria

- Ejecuta la herramienta seleccionada
- Almacena resultado en memoria FAISS
- Devuelve respuesta al usuario

## Comandos Disponibles

### Chat CLI

| Comando | Descripción |
|---------|-------------|
| `/model [openai\|deepseek\|openrouter]` | Cambiar proveedor LLM |
| `mcp list-tools` | Listar herramientas MCP disponibles |
| `historial` | Ver historial de la sesión |
| `herramientas` | Ver herramientas disponibles |
| `limpiar` | Limpiar pantalla |
| `ayuda` | Mostrar todos los comandos |
| `salir` | Terminar la conversación |

## Configuración

### Archivo .env (poc/.env)

```bash
# OpenWeatherMap API
OPENWEATHER_API_KEY=tu_api_key_aqui

# Proveedores LLM
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
OPENROUTER_API_KEY=sk-...

# Proveedor por defecto
CURRENT_LLM_PROVIDER=deepseek
```

### Configuración TOML (poc/agent-orquestador/config/prompts.toml)

El agente orquestador carga el prompt del sistema desde este archivo, permitiendo configurar fácilmente el comportamiento del LLM sin modificar código.

## Reglas Importantes para Agentes

### 1. NO Inventar Herramientas

El agente orquestador **NUNCA** debe inventar nombres de herramientas. Solo puede usar:

- `weather` → Agente meteorológico
- Herramientas MCP listadas en `list_mcp_tools()`
- `chat` → Conversación genérica

Si el usuario pide algo que no existe (ej: "calculadora", "buscar en web"), el agente debe responder que no tiene acceso a esa herramienta.

### 2. Validación de Herramientas

Antes de ejecutar cualquier herramienta MCP:
1. Verificar que la herramienta existe en `list_mcp_tools()`
2. Si no existe, devolver error con lista de herramientas disponibles
3. Nunca intentar ejecutar herramientas inventadas

### 3. Manejo de Errores

Si el LLM devuelve una respuesta inválida o vacía:
- Fallback a análisis por reglas (palabras clave)
- Loggear el error para depuración
- Devolver mensaje de error claro al usuario

## Estructura de Directorios

```
poc/
├── .env                          # Configuración compartida
├── agent-weather/                # Agente meteorológico
│   ├── src/
│   │   ├── agents/weather_agent.py
│   │   ├── services/weather_service.py
│   │   ├── services/deepseek_service.py
│   │   └── config.py
│   └── venv/
├── agent-orquestador/            # Agente orquestador LangGraph
│   ├── src/
│   │   ├── agents/orquestador_agent.py
│   │   └── services/
│   └── config/
│       └── prompts.toml          # Configuración de prompts
└── chatCLI/                      # Interfaz de chat
    ├── src/
    │   └── chat_cli.py           # Solo entrada/salida y memoria
    └── venv/

lib/mcp/                          # MCP Router (herramientas adicionales)
```

## Implementación con LangGraph

### StateGraph

El agente orquestador usa LangGraph para crear un flujo de ejecución:

```python
builder = StateGraph(OrquestadorState)
builder.add_node("analyze_intent", analyze_intent_node)
builder.add_node("execute_tool", execute_tool_node)
builder.set_entry_point("analyze_intent")
builder.add_edge("analyze_intent", "execute_tool")
builder.add_edge("execute_tool", END)
graph = builder.compile()
```

### Nodos del Grafo

1. **analyze_intent**: Analiza intención usando LLM
2. **execute_tool**: Ejecuta la herramienta seleccionada

## Ejemplos de Uso

### Ejemplo 1: Consulta de Clima

```
Usuario: "¿Cómo está el clima en Madrid?"
→ LLM analiza: weather_query con location=Madrid
→ Orquestador ejecuta agente meteorológico
→ Devuelve clima y recomendaciones
```

### Ejemplo 2: Saludo Multilingüe

```
Usuario: "say_hello(name=Juan, lang=es)"
→ LLM analiza: mcp con tool_name=say_hello
→ Orquestador ejecuta herramienta MCP
→ Devuelve "Hola Juan!"
```

### Ejemplo 3: Conversación General

```
Usuario: "Hola, ¿cómo estás?"
→ LLM analiza: chat (conversación general)
→ Orquestador responde desde el LLM
```

### Ejemplo 4: Herramienta Inexistente

```
Usuario: "Busca información en internet"
→ LLM podría intentar inventar "search_web"
→ Orquestador detecta que no existe
→ Devuelve: "No tengo acceso a herramienta de búsqueda web"
```

## Depuración

### Logs Habilitados

El sistema muestra:
- `✅ LLM Provider configurado...` - Confirmación de configuración
- `🧠 Agente orquestador: [herramienta] -> [intención]` - Herramienta usada
- `⚠️ Error...` - Advertencias de procesamiento

### Errores Comunes

1. **API Key inválida**: Verificar `.env`
2. **Herramienta no encontrada**: Verificar `list_mcp_tools()`
3. **Respuesta vacía del LLM**: Fallback a análisis por reglas
4. **Error en agente meteorológico**: Verificar OpenWeatherMap API

## Próximos Pasos

1. **Añadir más herramientas MCP**: Integrar nuevas funcionalidades
2. **Mejorar prompts**: Optimizar instrucciones del LLM
3. **Tests automatizados**: Verificar flujos de ejecución
4. **Interfaz web**: Crear UI amigable en lugar de CLI

## Versiones de LangGraph

El proyecto utiliza diferentes versiones de LangGraph según el agente:

| Agente | Versión LangGraph | Versión LangChain Core |
|--------|-------------------|------------------------|
| **Agent Orquestador** | 0.6.11 | 0.3.84 |
| **Agent Weather** | 0.0.30 | No especificada |
| **Chat CLI** | 0.0.30 | No especificada |

### Notas sobre Versiones

- **Agent Orquestador (v0.6.11)**: Versión más reciente con soporte completo para LangGraph
- **Agent Weather y Chat CLI (v0.0.30)**: Versión anterior, compatible con el código existente
- El agente orquestador está actualizado a la última versión para aprovechar características avanzadas de LangGraph

## Referencias

- LangGraph Documentation: https://langchain-ai.github.io/langgraph/
- OpenWeatherMap API: https://openweathermap.org/api
- DeepSeek API: https://platform.deepseek.com/
- MCP (Model Context Protocol): https://modelcontextprotocol.io/
