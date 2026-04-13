## [DECISION-006] Arquitectura de Configuración

- **Date:** 2026-04-12
- **Status:** accepted
- **Context:** Necesidad de separar configuración de código y secrets
- **Decision:** Usar estructura dual:
  - `poc/config.toml`: URLs, modelos, providers (versionado en git)
  - `.env`: API keys (NO versionado en git)
- **Consequences:**
  - Positivo: Mayor seguridad (API keys no en git)
  - Positivo: Configuración centralizada y versionable
  - Negativo: Requiere mantener dos archivos de config

## [DECISION-007] Agente de Seguridad (Guard Agent)

- **Date:** 2026-04-12
- **Status:** accepted
- **Context:** Necesidad de validar respuestas de agentes por seguridad
- **Decision:** Implementar `agent-guard` usando `openai/gpt-oss-safeguard-20b` de OpenRouter
- **Consequences:**
  - Positivo: Validación automatizada de seguridad
  - Positivo: Detección de contenido inapropiado, sesgos, privacidad
  - Negativo: Latencia adicional en el flujo del orquestador
  - Negativo: Costo adicional de API calls