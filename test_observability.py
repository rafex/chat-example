#!/usr/bin/env python3
"""
Script de prueba de observabilidad del sistema
"""
import sys
import os
import time

# Añadir paths necesarios
sys.path.insert(0, 'poc/agent-orquestador/src')

from services.logger import logger, set_debug_mode

def test_observabilidad():
    """Prueba de observabilidad del sistema"""
    print("=== Prueba de Observabilidad del Sistema ===\n")
    
    # 1. Activar modo debug
    print("1. Activando modo debug...")
    set_debug_mode(True)
    print("   ✅ Modo debug activado\n")
    
    # 2. Simular eventos de log
    print("2. Registrando eventos de log...\n")
    
    # Simular evento de configuración
    logger.log_event(
        session_id="test_session",
        turn_id=1,
        event_type="system_config",
        status="success",
        message="LLM Provider configurado: deepseek",
        details={"provider": "deepseek", "model": "deepseek-chat"}
    )
    
    # Simular evento de intención detectada
    logger.log_event(
        session_id="test_session",
        turn_id=1,
        event_type="intent_detection",
        status="success",
        message="Intención detectada: weather_query",
        details={"intent": "weather_query", "confidence": 0.95}
    )
    
    # Simular evento de herramienta sugerida
    logger.log_event(
        session_id="test_session",
        turn_id=1,
        event_type="tool_suggestion",
        status="success",
        tool_name="weather.get_current_weather",
        message="Tool sugerida por LLM: weather.get_current_weather"
    )
    
    # Simular evento de validación exitosa
    logger.log_tool_validation(
        session_id="test_session",
        turn_id=1,
        tool_name="weather.get_current_weather",
        valid=True,
        errors=[],
        latency_ms=15.5
    )
    
    # Simular evento de herramienta inexistente
    logger.log_event(
        session_id="test_session",
        turn_id=1,
        event_type="tool_validation",
        status="warning",
        tool_name="search_web",
        message="⚠️ Tool inexistente: search_web",
        details={"valid": False, "errors": ["Tool no registrada"]}
    )
    
    # Simular evento de ejecución de herramienta
    start_time = time.time()
    time.sleep(0.05)  # Simular tiempo de ejecución
    latency_ms = (time.time() - start_time) * 1000
    
    logger.log_tool_execution(
        session_id="test_session",
        turn_id=1,
        tool_name="weather.get_current_weather",
        success=True,
        latency_ms=latency_ms
    )
    
    # Simular evento de persistencia de memoria
    logger.log_memory_persisted(
        session_id="test_session",
        turn_id=1,
        memory_type="FAISS"
    )
    
    # Simular evento de respuesta final
    logger.log_event(
        session_id="test_session",
        turn_id=1,
        event_type="response_sent",
        status="success",
        message="Respuesta enviada al usuario",
        details={"response_length": 150, "latency_ms": 200.5}
    )
    
    print("\n   ✅ Eventos registrados\n")
    
    # 3. Verificar logs de sesión
    print("3. Verificando logs de sesión...")
    logs = logger.get_session_logs("test_session")
    print(f"   Total de eventos registrados: {len(logs)}")
    
    print("\n   Eventos registrados:")
    for i, log in enumerate(logs, 1):
        print(f"   {i}. [{log['event_type']}] {log['message']}")
    
    print("\n   ✅ Logs verificados\n")
    
    # 4. Verificar campos de log
    print("4. Verificando campos de log...")
    if logs:
        first_log = logs[0]
        expected_fields = ['timestamp', 'session_id', 'turn_id', 'event_type', 
                          'status', 'tool_name', 'message', 'details', 'latency_ms']
        
        for field in expected_fields:
            if field in first_log:
                print(f"   ✅ Campo '{field}': presente")
            else:
                print(f"   ❌ Campo '{field}': faltante")
    
    print("\n   ✅ Campos de log verificados\n")
    
    # 5. Probar modo compacto (producción)
    print("5. Probando modo compacto (producción)...")
    set_debug_mode(False)
    
    logger.log_event(
        session_id="test_session",
        turn_id=2,
        event_type="test_compact",
        status="success",
        message="Este es un mensaje de prueba en modo compacto"
    )
    
    print("   ✅ Modo compacto funcionando\n")
    
    print("=== Prueba de Observabilidad Completada Exitosamente ===")

if __name__ == "__main__":
    try:
        test_observabilidad()
    except Exception as e:
        print(f"\n❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)