# Agente Orquestador con LangGraph

Cerebro central del sistema que orquesta la ejecución de herramientas según la intención del usuario.

## Arquitectura

```
Usuario → Chat CLI → Agente Orquestador (LangGraph) → [Weather / MCP / Chat]
                        ↓
                     LLM (DeepSeek)
                        ↓
                  Análisis de Intención
```

**Características principales:**
- ✅ Usa LLM (DeepSeek) para analizar la intención del usuario
- ✅ Decisión inteligente de qué herramienta usar
- ✅ Fallback automático a análisis por reglas si LLM no está disponible
- ✅ Memoria de conversación con FAISS
- ✅ Integración con MCP Router para herramientas adicionales

## Instalación

```bash
cd poc/agent-orquestador
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Uso

### Probar agente orquestador

```bash
cd poc/agent-orquestador
source venv/bin/activate
python3 test_orquestador.py
```

### Probar con Chat CLI

```bash
cd poc/chatCLI
source venv/bin/activate
echo -e "¿Cómo está el clima en Madrid?\nsalir" | python src/chat_cli.py
```

## Comandos Disponibles

### En Chat CLI

1. **Consulta de clima**
   ```
   ¿Cómo está el clima en Madrid?
   ¿Qué tiempo hace en Barcelona?
   ```

2. **Comandos MCP directos**
   ```
   say_hello(name=Juan, lang=es)
   mcp list-tools
   ```

3. **Conversación general**
   ```
   Hola, ¿cómo estás?
   ```

## Estructura de Código

```
poc/agent-orquestador/
├── src/
│   ├── agents/
│   │   └── orquestador_agent.py    # LangGraph StateGraph
│   ├── schemas/
│   │   └── orquestador.py           # Modelos de datos
│   ├── services/
│   │   ├── weather_agent_wrapper.py # Wrapper agente meteorológico
│   │   └── mcp_wrapper.py           # Wrapper MCP
│   └── __init__.py
├── test_orquestador.py             # Pruebas unitarias
└── requirements.txt                # Dependencias
```

## Flujo de Ejecución

1. **Análisis de Intención**: Detecta palabras clave en la entrada
2. **Decisión de Herramienta**: Selecciona weather/mcp/chat según intención
3. **Ejecución**: Llama al wrapper correspondiente
4. **Formateo**: Convierte resultado a formato legible

## Dependencias

- langgraph >= 0.0.30
- pydantic >= 2.0.0
- python-dotenv >= 1.0.0
- requests >= 2.31.0
- numpy >= 1.24.0
- faiss-cpu >= 1.7.0

## Documentación

- `docs/agente-orquestador.md`: Documentación técnica completa
- `docs/mcp-architecture.md`: Arquitectura del sistema
