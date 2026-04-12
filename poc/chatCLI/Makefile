# Makefile para chatCLI
PYTHON := python3.14
VENV_DIR := venv
PIP := $(VENV_DIR)/bin/pip
PYTHON_VENV := $(VENV_DIR)/bin/python

.PHONY: all venv install test clean

all: venv install

venv:
	@echo "Creando entorno virtual para chatCLI..."
	$(PYTHON) -m venv $(VENV_DIR)

install: venv
	@echo "Instalando dependencias..."
	$(PIP) install -e ".[dev]"

test:
	@echo "Ejecutando pruebas..."
	$(PYTHON_VENV) -m pytest src/tests/ -v

clean:
	@echo "Limpiando..."
	rm -rf $(VENV_DIR)
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
