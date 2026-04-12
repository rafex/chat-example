# Makefile para construcción de proyectos Python
# Responsabilidad única: Build system (construcción y preparación)

.PHONY: all venv install check-python clean build-project

# Configuración
PYTHON := python3.14
PROJECTS := poc/agent-weather poc/agent-orquestador poc/chatCLI

# Por defecto: construir todos los proyectos
.PHONY: all
all: check-python
	@echo "Construyendo todos los proyectos..."
	@for project in $(PROJECTS); do \
		echo ""; \
		echo "=== Construyendo $$project ==="; \
		$(MAKE) -C $$project venv install || exit 1; \
	done
	@echo ""
	@echo "✅ Todos los proyectos construidos exitosamente"

# Verificar que Python 3.14 esté disponible
.PHONY: check-python
check-python:
	@echo "Verificando Python 3.14..."
	@if ! command -v $(PYTHON) >/dev/null 2>&1; then \
		echo "Error: Python 3.14 no encontrado."; \
		echo "Intentando detectar Homebrew en macOS..."; \
		if command -v brew >/dev/null 2>&1; then \
			BREW_PYTHON=$$(brew list python@3.14 --versions 2>/dev/null | head -n 1); \
			if [ -n "$$BREW_PYTHON" ]; then \
				echo "Python 3.14 detectado via Homebrew."; \
			else \
				echo "Python 3.14 no instalado via Homebrew. Ejecuta: brew install python@3.14"; \
				exit 1; \
			fi; \
		else \
			echo "Homebrew no detectado. Instala Python 3.14 manualmente."; \
			exit 1; \
		fi; \
	fi
	@echo "Python 3.14 OK: $$($(PYTHON) --version)"

# Construir un proyecto específico
.PHONY: build-project
build-project:
	@if [ -z "$(PROJECT)" ]; then \
		echo "Error: Debes especificar PROJECT=poc/agent-weather|poc/agent-orquestador|poc/chatCLI"; \
		exit 1; \
	fi
	@echo "Construyendo proyecto: $(PROJECT)"
	$(MAKE) -C $(PROJECT) venv install

# Limpiar todos los entornos
.PHONY: clean
clean:
	@echo "Limpiando entornos virtuales..."
	@for project in $(PROJECTS); do \
		if [ -d "$$project/venv" ]; then \
			echo "Eliminando $$project/venv"; \
			rm -rf $$project/venv; \
		fi; \
	done
	@echo "Limpiando cachés de Python..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Limpieza completada"
