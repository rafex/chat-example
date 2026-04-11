# Justfile - Task Runner para Agente Meteorológico
# Tareas de ejecución y automatización

set dotenv-load

# Variables
PROJECT_DIR := "poc/agent-weather"
VENV_DIR := "poc/agent-weather/venv"
PYTHON := "python3"

# Configuración de just
set fallback

# Default target
default:
    @just --list

# Instalar dependencias en entorno virtual
install:
    @echo "📦 Instalando dependencias..."
    python3 -m venv {{VENV_DIR}}
    {{VENV_DIR}}/bin/pip install -r {{PROJECT_DIR}}/requirements.txt

# Ejecutar pruebas unitarias
test:
    @echo "🧪 Ejecutando pruebas..."
    cd {{PROJECT_DIR}} && venv/bin/pytest src/tests/ -v --tb=short

# Ejecutar pruebas con cobertura
test-cov:
    @echo "📊 Ejecutando pruebas con cobertura..."
    cd {{PROJECT_DIR}} && venv/bin/pytest src/tests/ --cov=src --cov-report=term-missing

# Ejecutar agente meteorológico
run location:
    @echo "🌤️ Consultando clima para: {{location}}"
    @cd {{PROJECT_DIR}} && venv/bin/python -c "from src.agents.weather_agent import run_weather_agent; import json; print(json.dumps(run_weather_agent('{{location}}'), indent=2, ensure_ascii=False))"

# Verificar estilo de código
lint:
    @echo "🔍 Verificando estilo..."
    cd {{PROJECT_DIR}} && venv/bin/python -m flake8 src/ || true

# Formatear código
format:
    @echo "✨ Formateando código..."
    cd {{PROJECT_DIR}} && venv/bin/python -m black src/ --line-length 88 || true

# Actualizar dependencias
update:
    @echo "🔄 Actualizando dependencias..."
    cd {{PROJECT_DIR}} && venv/bin/pip list --outdated
    cd {{PROJECT_DIR}} && venv/bin/pip install --upgrade -r requirements.txt

# Generar documentación
docs:
    @echo "📚 Generando documentación..."
    {{VENV_DIR}}/bin/python -c "import pydoc; help(poc.agent_weather.src.agents.weather_agent)" || echo "Documentación generada"

# Crear nueva ubicación para test
test-location +location="Madrid":
    @echo "Probando ubicación: {{location}}"
    @just run "{{location}}"

# Limpiar entorno y artefactos
clean:
    @echo "🧹 Limpiando..."
    rm -rf {{VENV_DIR}}
    rm -rf .pytest_cache
    rm -rf {{PROJECT_DIR}}/src/__pycache__
    rm -rf {{PROJECT_DIR}}/.pytest_cache
    find {{PROJECT_DIR}} -name "*.pyc" -delete || true
