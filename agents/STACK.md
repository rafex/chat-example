# STACK

## Runtime
- Language: Python 3.14
- Framework: LangGraph 1.1.6

## Build & Dependencies
- Build: Makefile + justfile
- Dependency Management: pyproject.toml (PEP 621)
- Key dependencies:
  - langgraph==1.1.6
  - langchain-core>=1.2.0
  - pydantic==2.12.5
  - python-dotenv>=1.0.0

## Infrastructure
- Memoria semántica: FAISS (manejo manual con TF-IDF)
- Proveedores LLM: OpenAI, DeepSeek, OpenRouter
- API clima: OpenWeatherMap

## Project Structure
```
poc/
├── agent-weather/
│   ├── pyproject.toml
│   └── src/
├── agent-orquestador/
│   ├── pyproject.toml
│   └── src/
└── chatCLI/
    ├── pyproject.toml
    └── src/
```

## Constraints
- Python 3.14 requerido
- LangGraph 1.1.6 específico
- No usar SentenceTransformers (usar TF-IDF manual)
- Cada proyecto tiene su propio entorno virtual

## Modos de Operación
- **Strict**: Solo herramientas reales, no inventar capacidades, respuesta controlada
- **Flexible**: Permite respuesta conversacional adicional, útil para pruebas
- Configuración: `ORCHESTRATOR_MODE=strict|flexible` en `.env`
