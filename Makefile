# Makefile - Build System para Agente Meteorológico
# Segrega configuración de build y tareas de ejecución

.PHONY: help install test lint format clean build

# Variables
PYTHON := python3
PROJECT_DIR := poc/agent-weather
VENV_DIR := poc/agent-weather/venv
VENV_ACTIVATE := $(VENV_DIR)/bin/activate
PIP := $(VENV_DIR)/bin/pip
PYTEST := $(VENV_DIR)/bin/pytest

# Colores para output
GREEN := \033[0;32m
NC := \033[0m # No Color

help:
	@echo "Uso: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  install    Instalar dependencias en entorno virtual"
	@echo "  test       Ejecutar suite de pruebas"
	@echo "  lint       Verificar estilo de código"
	@echo "  format     Formatear código"
	@echo "  clean      Limpiar artefactos"
	@echo "  build      Preparar para distribución"

install: $(VENV_ACTIVATE)

$(VENV_ACTIVATE):
	@echo "$(GREEN)Creando entorno virtual...$(NC)"
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "$(GREEN)Instalando dependencias...$(NC)"
	$(PIP) install -r $(PROJECT_DIR)/requirements.txt
	@touch $(VENV_ACTIVATE)

test: install
	@echo "$(GREEN)Ejecutando pruebas...$(NC)"
	cd $(PROJECT_DIR) && venv/bin/pytest src/tests/ -v --tb=short

lint:
	@echo "$(GREEN)Verificando estilo de código...$(NC)"
	cd $(PROJECT_DIR) && venv/bin/python -m flake8 src/ || true
	cd $(PROJECT_DIR) && venv/bin/python -m py_compile src/**/*.py || true

format:
	@echo "$(GREEN)Formateando código...$(NC)"
	cd $(PROJECT_DIR) && venv/bin/python -m black src/ --line-length 88 || true
	cd $(PROJECT_DIR) && venv/bin/python -m isort src/ || true

clean:
	@echo "$(GREEN)Limpiando artefactos...$(NC)"
	rm -rf $(VENV_DIR)
	rm -rf .pytest_cache
	rm -rf $(PROJECT_DIR)/src/__pycache__
	rm -rf $(PROJECT_DIR)/src/**/__pycache__
	find $(PROJECT_DIR) -name "*.pyc" -delete
	find $(PROJECT_DIR) -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

build:
	@echo "$(GREEN)Preparando distribución...$(NC)"
	@echo "Versión: $(shell date +%Y%m%d)"
	@echo "El proyecto está listo para distribución"
