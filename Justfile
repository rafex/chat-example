# justfile para tareas operativas
# Responsabilidad única: Task runner (ejecución y tareas operativas)

set dotenv-load

# Variables
VENV_CHAT := "poc/chatCLI/venv"
VENV_WEATHER := "poc/agent-weather/venv"
VENV_ORQUESTADOR := "poc/agent-orquestador/venv"

# Configuración de just
set fallback

# Default target
_default:
    @just --list

# Configurar el entorno (llama a make)
setup:
    make all

# Ejecutar la aplicación CLI
run:
    {{VENV_CHAT}}/bin/python poc/chatCLI/src/chat_cli.py

# Ejecutar pruebas de cada proyecto
test-weather:
    {{VENV_WEATHER}}/bin/python -m pytest poc/agent-weather/src/tests/ -v

test-orquestador:
    {{VENV_ORQUESTADOR}}/bin/python -m pytest poc/agent-orquestador/src/tests/ -v

test-chat:
    {{VENV_CHAT}}/bin/python -m pytest poc/chatCLI/src/tests/ -v

test: test-weather test-orquestador test-chat

# Limpieza (delega en make)
clean:
    make clean

# Verificar entornos
check:
    @echo "=== Python Version ==="
    {{VENV_CHAT}}/bin/python --version
    {{VENV_WEATHER}}/bin/python --version
    {{VENV_ORQUESTADOR}}/bin/python --version
