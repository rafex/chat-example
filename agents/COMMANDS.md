# COMMANDS

## Development

### Build
```bash
# Construir todos los proyectos
make all
# o
just setup

# Construir proyecto específico
make build-project PROJECT=poc/agent-weather
```

### Run
```bash
# Ejecutar aplicación CLI
just run
```

### Test
```bash
# Ejecutar todas las pruebas
just test

# Ejecutar pruebas de proyecto específico
just test-weather
just test-orquestador
just test-chat
```

### Code Quality
```bash
# Linting (en cada proyecto)
cd poc/agent-weather && make venv && venv/bin/python -m flake8 src/

# Formateo (en cada proyecto)
cd poc/agent-weather && make venv && venv/bin/python -m black src/
```

### Clean
```bash
# Limpiar entornos y artefactos
make clean
# o
just clean
```

## Dependency Management
```bash
# Actualizar dependencias (editar pyproject.toml)
# Reinstalar
make build-project PROJECT=poc/agent-weather
```

## Database
No aplica - sistema usa memoria semántica FAISS.

## Docker
No aplica - proyecto es POC local.
