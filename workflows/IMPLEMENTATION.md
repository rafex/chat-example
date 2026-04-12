# IMPLEMENTATION

## Flujo de Desarrollo

1. **Leer `agents/SPEC.md`** — entender qué debe ser verdad cuando la iniciativa esté completa
2. **Leer `agents/DECISIONS.md`** — respetar restricciones arquitectónicas previas
3. **Leer `agents/CONVENTIONS.md`** — seguir naming y patrones del proyecto
4. **Explorar codebase** — usar `@audit` o `@explore` para entender estructura actual
5. **Aplicar skill `architect`** — si la tarea involucra nuevos módulos o interfaces
6. **Implementar en worktree** — usar skill `worktree` para cambios aislados
7. **Validar con `@audit`** — revisar calidad y seguridad
8. **Actualizar `agents/DECISIONS.md`** — si se toman decisiones persistentes nuevas
9. **Commit y PR** — usar conventional commits

## Ejemplo: Implementar TF-IDF

1. Leer `agents/STACK.md` para entender tecnologías actuales
2. Explorar `poc/agent-orquestador/src/memory/` para ver implementación actual
3. Aplicar skill `architect` para diseñar módulo TF-IDF
4. Implementar en worktree:
   - Crear `tfidf_service.py` con lógica de embeddings
   - Actualizar `semantic_memory.py` para usar TF-IDF
   - Escribir tests
5. Validar con `@audit`
6. Actualizar `agents/DECISIONS.md` con decisión de TF-IDF manual
7. Commit con mensaje: `feat: implementar TF-IDF manual para memoria semántica`
