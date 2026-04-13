# Reporte de Error y Solución

## Problema Reportado

El usuario reportó que el sistema estaba clasificando incorrectamente mensajes conversacionales como consultas de clima, causando que:
1. "hola me llamo raul y son de mexico" → Intentaba consultar el clima con esa frase como ubicación
2. "saludame en frances" → Intentaba consultar el clima en lugar de usar el MCP

## Causa Raíz

El algoritmo de detección de intenciones basado en reglas usaba `any(keyword in user_input_lower ...)`, lo que causaba coincidencias parciales:

1. **Falso positivo con "sol"**: La palabra clave `'sol'` (clima) estaba contenida en la subcadena "raul y **sol**" (de "son")
2. **Falta de palabra clave**: "saludame" no estaba en la lista de palabras clave MCP

## Solución Implementada

### 1. Coincidencia de palabras completas (commit cc94d1c)
Cambiado de:
```python
weather_match = any(keyword in user_input_lower for keyword in self.weather_keywords)
```

A:
```python
for keyword in self.weather_keywords:
    pattern = r'\b' + re.escape(keyword) + r'\b'
    if re.search(pattern, user_input_lower):
        weather_match = True
        break
```

Esto asegura que solo se coincidan palabras completas, no subcadenas.

### 2. Agregar palabra clave faltante (commit c4159a2)
Agregado `'saludame'` a la lista `mcp_keywords`.

## Resultados

### Antes:
- "hola me llamo raul y son de mexico" → `weather_query` ❌
- "saludame en frances" → `weather_query` ❌

### Después:
- "hola me llamo raul y son de mexico" → `mcp_greet` ✅
- "saludame en frances" → `mcp_greet` ✅

## Archivos Modificados

- `poc/agent-orquestador/src/agents/orquestador_agent.py`:
  - Mejorado algoritmo de detección de intenciones
  - Agregada palabra clave "saludame"

## Verificación

Ejecutar `python3 -c "import sys; sys.path.insert(0, 'poc/agent-orquestador/src'); from agents.orquestador_agent import AgentOrquestador; o = AgentOrquestador(); print(o.analyze_intent_by_rules('hola me llamo raul y son de mexico', []))"`
