# justfile para tareas operativas
# Responsabilidad única: Task runner (ejecución y tareas operativas)
# Las dependencias de construcción están en Makefile

set dotenv-load

# Variables de entornos virtuales
VENV_CHAT := "poc/chatCLI/venv"
VENV_WEATHER := "poc/agent-weather/venv"
VENV_ORQUESTADOR := "poc/agent-orquestador/venv"

# Configuración de just
set fallback

# Default target
_default:
    @just --list

# Configurar el entorno (delega en make - sistema de build)
setup:
    @echo "Configurando entornos virtuales..."
    make all

# Ejecutar la aplicación CLI
run:
    @echo "Iniciando Chat CLI..."
    {{VENV_CHAT}}/bin/python poc/chatCLI/src/chat_cli.py

# Ejecutar pruebas de cada proyecto
test-weather:
    @echo "Ejecutando pruebas de agent-weather..."
    {{VENV_WEATHER}}/bin/python -m pytest poc/agent-weather/src/tests/ -v

test-orquestador:
    @echo "Ejecutando pruebas de agent-orquestador..."
    {{VENV_ORQUESTADOR}}/bin/python -m pytest poc/agent-orquestador/src/tests/ -v

test-chat:
    @echo "Ejecutando pruebas de chatCLI..."
    {{VENV_CHAT}}/bin/python -m pytest poc/chatCLI/src/tests/ -v

# Ejecutar todas las pruebas
test: test-weather test-orquestador test-chat

# Limpieza (delega en make)
clean:
    @echo "Limpiando entornos virtuales..."
    make clean

# Verificar entornos
check:
    @echo "=== Verificación de Entornos Virtuales ==="
    @echo ""
    @echo "Chat CLI:"
    @if [ -d "{{VENV_CHAT}}" ]; then \
        {{VENV_CHAT}}/bin/python --version 2>/dev/null || echo "⚠️  Entorno no inicializado"; \
    else \
        echo "⚠️  Entorno no existe"; \
    fi
    @echo ""
    @echo "Agent Weather:"
    @if [ -d "{{VENV_WEATHER}}" ]; then \
        {{VENV_WEATHER}}/bin/python --version 2>/dev/null || echo "⚠️  Entorno no inicializado"; \
    else \
        echo "⚠️  Entorno no existe"; \
    fi
    @echo ""
    @echo "Agent Orquestador:"
    @if [ -d "{{VENV_ORQUESTADOR}}" ]; then \
        {{VENV_ORQUESTADOR}}/bin/python --version 2>/dev/null || echo "⚠️  Entorno no inicializado"; \
    else \
        echo "⚠️  Entorno no existe"; \
    fi

# Listar herramientas disponibles
tools:
    @echo "Herramientas disponibles en orquestador:"
    @if [ -d "{{VENV_ORQUESTADOR}}" ]; then \
        {{VENV_ORQUESTADOR}}/bin/python -c "from src.registry.tool_registry import tool_registry; tool_registry.list_tools()" 2>/dev/null || echo "⚠️  No se pudo cargar el registro de herramientas"; \
    else \
        echo "⚠️  Entorno no existe"; \
    fi

# Limpiar memoria semántica
clean-memory:
    @echo "Limpiando memoria semántica..."
    @if [ -d "{{VENV_ORQUESTADOR}}" ]; then \
        {{VENV_ORQUESTADOR}}/bin/python -c "from src.services.memory_service import clear_memory_cache; clear_memory_cache(); print('✅ Memoria limpiada')" 2>/dev/null || echo "⚠️  No se pudo limpiar la memoria"; \
    else \
        echo "⚠️  Entorno no existe"; \
    fi

# Verificar estado de la memoria
memory-status:
    @echo "Estado del servicio de memoria:"
    @if [ -d "{{VENV_ORQUESTADOR}}" ]; then \
        {{VENV_ORQUESTADOR}}/bin/python -c "\
import os; \
from pathlib import Path; \
memory_dir = Path.home() / '.agentes-langgraph' / 'memory'; \
if memory_dir.exists(): \
    files = list(memory_dir.glob('*.faiss')); \
    print(f'✅ Índices FAISS encontrados: {len(files)}'); \
    for f in files: \
        print(f'  - {f.name} ({f.stat().st_size / 1024:.1f} KB)'); \
else: \
    print('ℹ️  No se encontró directorio de memoria')" 2>/dev/null || echo "⚠️  No se pudo verificar el estado"; \
    else \
        echo "⚠️  Entorno no existe"; \
    fi

# Cambiar modo de operación
mode MODE:
    @echo "Cambiando modo de operación a: {{MODE}}"
    @if [ "{{MODE}}" != "strict" ] && [ "{{MODE}}" != "flexible" ]; then \
        echo "❌ Modo inválido. Usar 'strict' o 'flexible'"; \
        exit 1; \
    fi
    @if [ -f ".env" ]; then \
        sed -i.bak 's/ORCHESTRATOR_MODE=.*/ORCHESTRATOR_MODE={{MODE}}/' .env && \
        echo "✅ Modo cambiado a {{MODE}}"; \
    else \
        echo "⚠️  No se encontró .env. Creando uno basado en .env.example"; \
        cp poc/.env.example .env && \
        sed -i.bak 's/ORCHESTRATOR_MODE=.*/ORCHESTRATOR_MODE={{MODE}}/' .env && \
        echo "✅ .env creado y modo configurado a {{MODE}}"; \
    fi

# Verificar modo actual
mode-status:
    @echo "Modo de operación actual:"
    @if [ -f ".env" ]; then \
        grep "ORCHESTRATOR_MODE" .env || echo "⚠️  No se encontró configuración de modo"; \
    else \
        echo "⚠️  No se encontró .env. Modo por defecto: strict"; \
    fi

# Limpiar sesiones activas
clean-sessions:
    @echo "Limpiando sesiones activas..."
    @if [ -d "poc/agent-orquestador/venv" ]; then \
        poc/agent-orquestador/venv/bin/python -c "from src.services.session_service import cleanup_sessions; cleanup_sessions(); print('✅ Sesiones limpiadas')" 2>/dev/null || echo "⚠️  No se pudieron limpiar las sesiones"; \
    else \
        echo "⚠️  Entorno no existe"; \
    fi
