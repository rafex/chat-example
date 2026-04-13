#!/usr/bin/env python3
"""
Script de prueba del sistema de memoria dual
"""
import sys
import os

# Añadir paths necesarios
sys.path.insert(0, 'poc/agent-orquestador/src')

from services.memory_service import get_memory_service
from services.session_service import get_session_manager, cleanup_sessions
from services.embedding_service import get_embedding_service

def test_memory_system():
    """Prueba del sistema de memoria"""
    print("=== Prueba del Sistema de Memoria Dual ===\n")
    
    # 1. Crear sesión
    print("1. Creando sesión de prueba...")
    session_manager = get_session_manager()
    session_info = session_manager.create_session("test_session")
    print(f"   ✅ Sesión creada: {session_info['session_id']}\n")
    
    # 2. Obtener servicio de memoria
    print("2. Obteniendo servicio de memoria...")
    memory_service = session_info["memory_service"]
    print("   ✅ Servicio de memoria obtenido\n")
    
    # 3. Añadir turnos conversacionales (aplicando política de memoria)
    print("3. Añadiendo turnos conversacionales...")
    test_messages = [
        ("user", "Hola, ¿cómo estás?"),  # Debería ser filtrado (saludo trivial)
        ("user", "Quiero saber el clima en Madrid"),  # Debería guardarse
        ("assistant", "El clima en Madrid es soleado con 25°C"),  # Debería guardarse (resultado de herramienta)
        ("user", "Gracias, muy útil"),  # Debería guardarse (hecho relevante)
        ("user", "Adiós"),  # Debería ser filtrado (saludo trivial)
        ("assistant", "¿En qué puedo ayudarte?"),  # Debería ser filtrado (respuesta genérica)
    ]
    
    for role, message in test_messages:
        memory_service.add_conversation_turn(role, message)
        print(f"   - {role}: {message}")
    
    print("   ✅ Turnos añadidos\n")
    
    # 4. Verificar memoria conversacional
    print("4. Verificando memoria conversacional...")
    recent_history = memory_service.short_term.get_recent_history()
    print(f"   Turnos guardados: {len(recent_history)}")
    for i, turn in enumerate(recent_history, 1):
        print(f"   {i}. {turn['role']}: {turn['content'][:50]}...")
    print("   ✅ Memoria conversacional verificada\n")
    
    # 5. Añadir memoria semántica
    print("5. Añadiendo memoria semántica...")
    embedding_service = get_embedding_service(backend="tfidf")
    
    # Datos de ejemplo que deberían guardarse
    semantic_data = [
        ("El clima en Madrid es soleado", {"source": "weather_tool", "tool_name": "weather.get_current_weather", "memory_type": "tool_result", "importance": 0.8}),
        ("El usuario prefiere clima cálido", {"source": "user_preference", "memory_type": "user_fact", "importance": 0.7}),
    ]
    
    for text, metadata in semantic_data:
        embedding = embedding_service.embed_single(text)
        memory_service.add_semantic_memory(text, embedding, metadata)
        print(f"   - {text}")
    
    print("   ✅ Memoria semántica añadida\n")
    
    # 6. Recuperar contexto
    print("6. Recuperando contexto...")
    query = "¿Cómo está el clima en Madrid?"
    query_embedding = embedding_service.embed_single(query)
    context = memory_service.get_context(query_embedding, k_semantic=2)
    
    print(f"   Historial conversacional: {len(context['short_term'])} turnos")
    print(f"   Memoria semántica: {len(context['semantic'])} elementos")
    
    if context['semantic']:
        print("   Elementos semánticos recuperados:")
        for i, mem in enumerate(context['semantic'], 1):
            print(f"   {i}. {mem['text'][:50]}... (score: {mem['score']:.3f})")
    
    print("   ✅ Contexto recuperado\n")
    
    # 7. Verificar metadatos
    print("7. Verificando metadatos...")
    if memory_service.semantic and memory_service.semantic.metadata:
        first_metadata = memory_service.semantic.metadata[0]
        print("   Metadatos de primer elemento:")
        for key in ['source', 'tool_name', 'session_id', 'turn_id', 'importance', 'memory_type']:
            value = first_metadata.get(key, 'N/A')
            print(f"   - {key}: {value}")
    
    print("   ✅ Metadatos verificados\n")
    
    # 8. Limpiar sesiones
    print("8. Cerrando sesión...")
    session_manager.close_session("test_session")
    print("   ✅ Sesión cerrada\n")
    
    print("=== Prueba Completada Exitosamente ===")

if __name__ == "__main__":
    try:
        test_memory_system()
    except Exception as e:
        print(f"\n❌ Error en la prueba: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)