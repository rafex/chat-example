# AGENTS.md - Guía para Agentes de IA

## Visión General del Proyecto

Este proyecto es una **Proof of Concept (POC)** para construir un sistema de chat inteligente basado en **LangGraph**, con una arquitectura orientada a **orquestación de herramientas reales**, **memoria semántica** y **control explícito del flujo de decisión**.

El objetivo no es crear un chatbot enfocado en una sola tarea, como responder únicamente sobre el clima, sino demostrar cómo un **agente orquestador o maestro** puede decidir, validar y usar distintas herramientas disponibles para resolver solicitudes del usuario sin inventar capacidades inexistentes.

## Objetivos del Proyecto

### Objetivos funcionales

1. Proveer una **interfaz de entrada y salida de texto** para conversación con el usuario.
2. Incorporar **memoria semántica usando FAISS** para recuperar contexto relevante.
3. Usar un **agente orquestador** que decida cuándo responder directamente y cuándo usar una herramienta.
4. Integrar **herramientas reales disponibles**, como:
   - un agente especializado de clima,
   - herramientas expuestas vía MCP,
   - un fallback conversacional.
5. Evitar que el sistema invente herramientas, MCPs o capacidades que no existan.
6. Usar **LangGraph** para modelar el flujo del agente como un grafo de estados.

### Objetivos técnicos

1. Mantener una **separación clara de responsabilidades** entre chat, memoria, orquestación y herramientas.
2. Definir un **catálogo real de herramientas** como fuente única de verdad.
3. Validar de forma determinista cualquier decisión producida por el LLM.
4. Separar **memoria corta conversacional** de **memoria semántica recuperada por embeddings**.
5. Incorporar manejo explícito de errores, fallback y observabilidad.
6. Hacer que el flujo sea trazable, testeable y extensible.

---

## Principio Central del Proyecto

Este proyecto sigue una idea principal:

> El orquestador no debe responder "como si supiera hacer algo", sino decidir si existe una herramienta real disponible para resolver la necesidad del usuario, validarla y ejecutarla de forma controlada.

Eso significa que:

- el sistema **no debe inventar MCPs**;
- el sistema **no debe inventar nombres de tools**;
- el sistema **no debe asumir acceso a web, cálculo, archivos o APIs no integradas**;
- el sistema debe ser capaz de decir claramente:
  **"No tengo acceso a esa capacidad en esta versión"**.

---

## Arquitectura General

### Flujo conceptual

```text
Usuario
  ↓
Chat CLI
  ↓
Carga de contexto local
  ↓
Recuperación de memoria relevante (FAISS)
  ↓
Agente Orquestador (LangGraph)
  ↓
Análisis de intención con LLM
  ↓
Validación determinista de herramienta y argumentos
  ↓
Enrutamiento
  ├─ Ejecutar herramienta real
  └─ Responder como chat genérico
  ↓
Formateo de respuesta
  ↓
Persistencia en memoria
  ↓
Respuesta al usuario
```

---

## Componentes del Sistema

### 1. Chat CLI (`poc/chatCLI/`)

**Responsabilidades:**
- Entrada y salida de texto con el usuario
- Lectura del historial reciente
- Integración con memoria FAISS
- Invocación del agente orquestador
- Visualización de herramientas disponibles y logs básicos

**Restricciones:**
- No tiene lógica de inferencia propia
- No decide herramientas
- No ejecuta lógica de negocio

El Chat CLI es una capa de interacción, no un agente autónomo.

---

### 2. Agente Orquestador (`poc/agent-orquestador/`)

**Responsabilidades:**
- Cargar el contexto necesario para el turno actual
- Analizar la intención del usuario usando un LLM
- Decidir si debe usar una herramienta o responder directamente
- Validar determinísticamente que la decisión sea válida
- Ejecutar la herramienta correcta o hacer fallback
- Consolidar la respuesta final
- Coordinar la persistencia de memoria

**Restricciones:**
- No debe inventar herramientas
- No debe ejecutar una tool no registrada
- No debe confiar ciegamente en el JSON del LLM
- No debe mezclar verdad del sistema con prompt del sistema

El orquestador usa LangGraph como motor de control del flujo.

---

### 3. Herramientas Especializadas

**Agente meteorológico** (`poc/agent-weather/`)
Herramienta especializada para obtener información climática usando OpenWeatherMap.

**MCP Router** (`lib/mcp/`)
Punto de acceso a herramientas expuestas vía MCP, como por ejemplo saludos multilingües.

**Chat genérico**
Respuesta conversacional cuando:
- no se necesita una herramienta,
- no existe una herramienta adecuada,
- o se decide operar en modo conversacional.

---

### 4. Memoria

El proyecto debe distinguir dos tipos de memoria:

**Memoria corta conversacional**
Sirve para continuidad inmediata:
- últimos turnos
- contexto reciente
- referencias temporales o de seguimiento
- estado actual de la conversación

**Memoria semántica con FAISS**
Sirve para recuperación relevante:
- hechos anteriores útiles
- resultados importantes de herramientas
- contexto histórico persistente
- información útil para resolver nuevos turnos

**Importante**
FAISS no debe reemplazar por completo el historial reciente.
Ambas memorias deben convivir.

---

## Contrato de Herramientas

Todas las herramientas deben presentarse al orquestador de forma uniforme.

Cada herramienta debería exponer al menos:
- `name`
- `description`
- `kind`
- `input_schema`
- `output_schema`
- `available`
- `timeout`

**Ejemplo conceptual**
```json
{
    "name": "weather.get_current_weather",
    "description": "Obtiene el clima actual para una ciudad",
    "kind": "agent",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {"type": "string"}
        },
        "required": ["location"]
    },
    "output_schema": {
        "type": "object"
    },
    "available": true,
    "timeout": 10
}
```

---

## Registro Único de Herramientas

El sistema debe tener un tool registry central.

**Ejemplo conceptual:**
```python
TOOLS = {
    "weather.get_current_weather": WeatherToolAdapter(...),
    "mcp.say_hello": McpToolAdapter(...),
    "chat.respond": GenericChatResponder(...)
}
```

Este registro debe ser la fuente de verdad para:
- el prompt del orquestador
- la validación de herramientas
- la ejecución real
- el comando CLI herramientas
- la depuración del sistema

**Regla crítica**
El LLM puede sugerir una herramienta.
Solo el registro determina si esa herramienta realmente existe.

---

## Flujo de Decisión del Orquestador

El proceso debe dividirse en tres capas.

### Capa A: Interpretación del LLM
El LLM recibe:
- prompt del sistema
- herramientas disponibles
- historial reciente
- memoria recuperada
- mensaje actual del usuario

Y devuelve una decisión estructurada.

### Capa B: Validación determinista
Antes de ejecutar cualquier cosa, el sistema valida:
- que la herramienta exista
- que la herramienta esté disponible
- que los argumentos requeridos estén presentes
- que los tipos sean correctos
- que el nombre coincida exactamente con una tool real
- que la solicitud no requiera una capacidad inexistente

### Capa C: Ejecución
Solo si la validación fue exitosa:
- se ejecuta la herramienta
- se normaliza la respuesta
- se persiste lo necesario en memoria

---

## Formato Esperado del JSON del LLM

El LLM debe responder con un JSON estricto y fácil de validar.

**Ejemplo cuando sí aplica una herramienta**
```json
{
  "intent": "weather_query",
  "tool_type": "weather",
  "tool_name": "weather.get_current_weather",
  "arguments": {
    "location": "Madrid"
  },
  "confidence": 0.95,
  "requires_tool": true,
  "reasoning_summary": "El usuario solicita información climática actual",
  "missing_arguments": []
}
```

**Ejemplo cuando no existe capacidad real**
```json
{
  "intent": "external_search",
  "tool_type": "none",
  "tool_name": null,
  "arguments": {},
  "confidence": 0.71,
  "requires_tool": false,
  "reasoning_summary": "El usuario pide búsqueda web, pero no existe esa herramienta en esta versión",
  "missing_arguments": []
}
```

**Regla importante**
Este JSON no se ejecuta directamente.
Primero pasa por validación determinista.

---

## Política de Enrutamiento

El orquestador debe seguir reglas explícitas.

**Debe usar herramienta cuando:**
- la petición requiere datos externos
- existe una herramienta real adecuada
- los argumentos mínimos están presentes o pueden inferirse con seguridad

**Debe responder directamente como chat cuando:**
- la petición es social o conversacional
- no necesita una herramienta
- la herramienta no existe y conviene explicar el límite del sistema
- el modo flexible lo permite

**Debe pedir precisión cuando:**
- falta un argumento clave
- el usuario es ambiguo
- ejecutar una herramienta sin aclaración puede producir un resultado incorrecto

---

## Reglas Importantes para Agentes

### 1. No inventar herramientas

El orquestador nunca debe inventar:
- nombres de MCPs
- nombres de tools
- APIs no integradas
- capacidades no registradas

Si el usuario pide algo no disponible, el sistema debe responder de forma clara.

**Ejemplo:**
> "Puedo ayudarte con conversación general, clima y las herramientas MCP disponibles actualmente. No tengo acceso a búsqueda web ni calculadora en esta versión."

---

### 2. Validar antes de ejecutar

Antes de usar una herramienta MCP o cualquier otra:
1. Verificar que existe en el registro
2. Verificar que está disponible
3. Validar argumentos
4. Respetar timeouts y límites
5. Si no es válida, devolver un error controlado

---

### 3. No confiar ciegamente en el LLM

El LLM puede:
- Devolver JSON inválido
- Sugerir una herramienta inventada
- Proponer argumentos incompletos
- Confundir intención con capacidad

Por eso, toda decisión del LLM debe pasar por validación estructurada y fallback.

---

### 4. Manejar el error como parte normal del flujo

El sistema debe contemplar al menos:
- `tool_not_found`
- `tool_unavailable`
- `invalid_arguments`
- `tool_timeout`
- `tool_execution_error`
- `llm_parse_error`
- `memory_retrieval_error`
- `faiss_empty_index`
- `embedding_error`

Cada uno debe tener un comportamiento definido.

---

### 5. Separar capacidad real del prompt

La verdad del sistema vive en:
- el registro de herramientas
- los validadores
- los adaptadores
- el estado del grafo

El prompt solo comunica esa realidad al LLM.
El prompt no define por sí mismo lo que el sistema puede hacer.

---

## Política de Memoria

**Qué sí guardar**
- Resultados útiles de herramientas
- Hechos relevantes del usuario
- Preferencias persistentes
- Decisiones importantes
- Contexto que ayude a futuras interacciones

**Qué no guardar**
- Saludos triviales
- Respuestas duplicadas
- Errores internos sin valor futuro
- Ruido conversacional irrelevante

**Metadatos recomendados por memoria**
- `source`
- `tool_name`
- `timestamp`
- `session_id`
- `turn_id`
- `importance`
- `memory_type`

---

## Observabilidad y Depuración

El sistema debe poder mostrar, al menos en modo debug:
- Mensaje recibido
- Memoria recuperada
- Herramientas disponibles en ese turno
- Decisión del LLM
- Resultado de validación
- Herramienta ejecutada
- Tiempo de ejecución
- Respuesta final
- Persistencia en memoria

**Campos de log sugeridos**
- `session_id`
- `turn_id`
- `event_type`
- `tool_name`
- `status`
- `latency_ms`

**Ejemplos de logs**
```
✅ LLM Provider configurado: deepseek
🧠 Intención detectada: weather_query
🔎 Tool sugerida por LLM: weather.get_current_weather
✅ Tool validada
⚠️ Tool inexistente: search_web
💾 Memoria persistida en FAISS
```

---

## Implementación con LangGraph

LangGraph debe aportar valor real al flujo del sistema.

**Grafo recomendado**
```text
START
  ↓
load_context
  ↓
retrieve_memory
  ↓
analyze_intent
  ↓
validate_decision
  ↓
route_request
  ├─ execute_tool
  └─ generic_chat
  ↓
format_response
  ↓
persist_memory
  ↓
END
```

**Nodos sugeridos**

1. **load_context**
   Carga historial reciente y configuración activa.

2. **retrieve_memory**
   Recupera memoria semántica relevante desde FAISS.

3. **analyze_intent**
   Usa LLM para proponer intención, herramienta y argumentos.

4. **validate_decision**
   Valida determinísticamente la decisión del LLM.

5. **route_request**
   Decide si ejecutar tool o responder con chat.

6. **execute_tool**
   Ejecuta la herramienta real seleccionada.

7. **generic_chat**
   Genera respuesta conversacional sin tool.

8. **format_response**
   Homologa la salida final al usuario.

9. **persist_memory**
   Decide qué guardar y cómo guardarlo.

---

## Estado del Grafo

El estado del orquestador debería ser explícito y trazable.

**Campos sugeridos para OrquestadorState**
- `session_id`
- `turn_id`
- `user_message`
- `conversation_history`
- `retrieved_memories`
- `available_tools`
- `llm_decision`
- `validated_tool`
- `tool_result`
- `final_response`
- `errors`

Mientras más explícito sea el estado, más fácil será:
- depurar
- probar
- extender
- auditar el comportamiento del agente

---

## Estructura de Directorios

```
poc/
├── .env
├── agent-weather/
│   ├── src/
│   │   ├── agents/weather_agent.py
│   │   ├── services/weather_service.py
│   │   ├── services/deepseek_service.py
│   │   └── config.py
│   └── venv/
├── agent-orquestador/
│   ├── src/
│   │   ├── agents/orquestador_agent.py
│   │   ├── services/
│   │   ├── registry/              <-- NUEVO: Registro de herramientas
│   │   ├── validators/            <-- NUEVO: Validadores
│   │   └── state/
│   └── config/
│       └── prompts.toml
└── chatCLI/
    ├── src/
    │   └── chat_cli.py
    └── venv/

lib/
└── mcp/
```

---

## Configuración

**Archivo `.env`**
```bash
# OpenWeatherMap API
OPENWEATHER_API_KEY=tu_api_key_aqui

# Proveedores LLM
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
OPENROUTER_API_KEY=sk-...

# Proveedor actual
CURRENT_LLM_PROVIDER=deepseek

# Modo de operación
ORCHESTRATOR_MODE=strict
```

**Archivo `prompts.toml`**
El prompt del sistema debe residir en:
`poc/agent-orquestador/config/prompts.toml`

Este archivo debe describir:
- el rol del orquestador
- las herramientas disponibles
- el formato del JSON esperado
- las restricciones de no inventar herramientas

---

## Modos de Operación

**Modo strict**
- solo usa herramientas reales
- no improvisa capacidades
- si no hay herramienta válida, informa el límite del sistema
- ideal para validar el comportamiento del orquestador

**Modo flexible**
- permite respuesta conversacional adicional
- útil para pruebas exploratorias
- aun así no debe inventar herramientas inexistentes

---

## Ejemplos de Uso

### Ejemplo 1: consulta de clima
Usuario: ¿Cómo está el clima en Madrid?
→ El orquestador detecta intención meteorológica
→ Valida la tool weather.get_current_weather
→ Ejecuta la herramienta
→ Devuelve clima y sugerencias

### Ejemplo 2: saludo vía MCP
Usuario: say_hello(name=Juan, lang=es)
→ El orquestador detecta intención de tool MCP
→ Valida que mcp.say_hello exista
→ Ejecuta la herramienta
→ Devuelve: Hola Juan

### Ejemplo 3: conversación general
Usuario: Hola, ¿cómo estás?
→ El orquestador detecta conversación social
→ No requiere herramienta
→ Responde por chat genérico

### Ejemplo 4: herramienta inexistente
Usuario: Busca información en internet
→ El LLM podría sugerir una tool como search_web
→ La validación detecta que no existe
→ Respuesta: No tengo acceso a búsqueda web en esta versión

### Ejemplo 5: argumento faltante
Usuario: ¿Cómo está el clima?
→ Existe intención meteorológica
→ Falta location
→ El sistema pide precisión antes de ejecutar

---

## Seguridad y Límites

Aunque sea una POC, el sistema debe contemplar:
- lista blanca de herramientas
- validación estricta de argumentos
- timeouts por herramienta
- límites de reintentos
- sanitización de input
- límite de tamaño de contexto
- límite de memoria recuperada
- protección contra prompt injection proveniente de tools

**Regla crítica**
La salida de una herramienta no debe pasar al modelo sin control si contiene instrucciones maliciosas o irrelevantes.

---

## Estrategia de Pruebas

Las pruebas deben cubrir escenarios, no solo funciones aisladas.

**Casos felices**
- clima → usa weather
- saludo → usa MCP
- conversación general → usa chat

**Casos límite**
- herramienta inventada por el LLM
- MCP existente con argumentos incompletos
- clima sin location
- timeout de herramienta
- JSON inválido del LLM
- FAISS sin resultados

**Casos de continuidad**
- pregunta inicial
- seguimiento con contexto implícito
- recuperación correcta de memoria

---

## Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `/model [openai\|deepseek\|openrouter]` | Cambia el proveedor LLM |
| `mcp list-tools` | Lista las herramientas MCP disponibles |
| `historial` | Muestra historial de la sesión |
| `herramientas` | Muestra herramientas registradas |
| `limpiar` | Limpia la pantalla |
| `ayuda` | Muestra los comandos disponibles |
| `salir` | Termina la conversación |

---

## Criterios de Éxito de la POC

La POC se considera exitosa si demuestra que:
1. El sistema no inventa herramientas
2. El orquestador usa la herramienta correcta en escenarios esperados
3. El sistema puede responder de forma controlada cuando no existe capacidad
4. La memoria ayuda en conversaciones de seguimiento
5. El flujo LangGraph es visible, trazable y depurable
6. Los errores se manejan como parte normal del flujo y no como fallos caóticos
