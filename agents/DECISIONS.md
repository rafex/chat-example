# DECISIONS

## [DECISION-001] Uso de SentenceTransformers para embeddings

- **Date:** 2026-04-12
- **Status:** accepted
- **Context:** Necesidad de embeddings de alta calidad para memoria semántica con FAISS.
- **Decision:** Usar SentenceTransformers como backend principal para embeddings, con TF-IDF como fallback automático.
- **Consequences:**
  - Positivo: Mejor calidad de embeddings que TF-IDF manual
  - Positivo: Embeddings de dimensión fija (384) para consistencia
  - Positivo: Fallback automático a TF-IDF si SentenceTransformers no está disponible
  - Negativo: Requiere instalación de bibliotecas adicionales (torch, sentence-transformers)

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
- **Status:** accepted
- **Context:** Necesidad de controlar el comportamiento del orquestador según el entorno (producción vs pruebas).
- **Decision:** Implementar dos modos de operación configurables mediante variable de entorno:
  - **Modo Strict:** Solo usa herramientas reales, no inventa capacidades, respuesta controlada cuando no existe herramienta. Ideal para producción.
  - **Modo Flexible:** Permite respuesta conversacional adicional, útil para pruebas exploratorias. Aun así no inventa herramientas inexistentes.
- **Consequences:**
  - Positivo: Mayor control sobre comportamiento del sistema según entorno
  - Positivo: Flexibilidad para pruebas sin sacrificar seguridad
  - Negativo: Complejidad adicional mínima en el código
- **Implementación:**
  - Variable de entorno: `ORCHESTRATOR_MODE=strict|flexible`
  - Servicio `config_service.py` para gestionar configuración
  - Lógica en `route_request_node` y `generic_chat_node`
  - Comandos Justfile: `just mode strict|flexible`, `just mode-status`

## [DECISION-005] Arquitectura de Memoria Dual

- **Date:** 2026-04-12
- **Status:** accepted
- **Context:** Necesidad de mantener contexto conversacional inmediato y recuperación semántica de información relevante.
- **Decision:** Implementar sistema de memoria dual que combine:
  1. **Memoria Corta Conversacional:** Últimos turnos para continuidad inmediata
  2. **Memoria Semántica con FAISS:** Recuperación de hechos históricos relevantes
  
  **Regla clave:** FAISS no debe reemplazar el historial reciente. Ambas memorias deben convivir.
- **Consequences:**
  - Positivo: Mejor contexto para el LLM sin perder información relevante histórica
  - Positivo: Separación clara entre contexto inmediato y conocimiento persistente
  - Negativo: Complejidad adicional en la implementación
  - Negativo: Requiere gestión de embeddings y vector store
- **Implementación:**
  - Servicio `MemoryService` con `ShortTermMemory` y `SemanticMemory`
  - Integración en `retrieve_memory_node` del orquestador
  - Persistencia automática de índices FAISS en `~/.agentes-langgraph/memory/`
