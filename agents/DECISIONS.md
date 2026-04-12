# DECISIONS

## [DECISION-001] Uso de TF-IDF Manual en lugar de SentenceTransformers

- **Date:** 2026-04-12
- **Status:** accepted
- **Context:** La biblioteca SentenceTransformers no está disponible en el entorno actual. Se necesita una solución de embeddings para memoria semántica.
- **Decision:** Implementar TF-IDF manualmente para generar embeddings y recuperación de memoria semántica.
- **Consequences:**
  - Positivo: No requiere instalación de bibliotecas externas adicionales
  - Positivo: Mayor control sobre el proceso de embedding
  - Negativo: Menor precisión que modelos pre-entrenados
  - Negativo: Requiere implementación manual de lógica de similitud

## [DECISION-002] Estructura de Proyecto SpecNative

- **Date:** 2026-04-12
- **Status:** accepted
- **Context:** Necesidad de documentación estructurada para agentes de IA.
- **Decision:** Adoptar estructura SpecNative con `agents/`, `tasks/`, `workflows/`.
- **Consequences:**
  - Positivo: Documentación clara y estructurada
  - Positivo: Separación de responsabilidades
  - Negativo: Requiere mantenimiento adicional

## [DECISION-003] Uso de Python 3.14

- **Date:** 2026-04-12
- **Status:** accepted
- **Context:** El proyecto requiere características modernas de Python.
- **Decision:** Python 3.14 es la versión mínima requerida.
- **Consequences:**
  - Positivo: Acceso a características modernas de Python
  - Negativo: Requiere instalación específica de Python 3.14

## [DECISION-004] Modos de Operación (Strict/Flexible)

- **Date:** 2026-04-12
- **Status:** pending
- **Context:** Documentación menciona modos `strict` y `flexible`, pero no están implementados.
- **Decision:** Pendiente de implementación. Los modos deben controlar:
  - **Modo Strict:** Solo herramientas reales, no inventar capacidades, respuesta controlada cuando no existe herramienta
  - **Modo Flexible:** Permite respuesta conversacional adicional, útil para pruebas exploratorias
- **Consequences:**
  - Positivo: Mayor control sobre comportamiento del sistema
  - Negativo: Requiere implementación en orquestador y validadores
  - **Acción requerida:** Implementar variable de entorno `ORCHESTRATOR_MODE=strict|flexible`
