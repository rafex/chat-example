#!/usr/bin/env python3
"""
Script de prueba para el Agente Orquestador
"""

import sys
import os

# Configurar paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

try:
    from src.agents.orquestador_agent import run_orquestador, AgentOrquestador
    
    print("=" * 60)
    print("🎯 PRUEBA DEL AGENTE ORQUESTADOR")
    print("=" * 60)
    
    # Test 1: Consulta de clima
    print("\n📌 Test 1: Consulta de clima en Madrid")
    result = run_orquestador("¿Cómo está el clima en Madrid?")
    if result.get('success'):
        print(f"Intent: {result.get('intent')}")
        print(f"Tool used: {result.get('tool_used')}")
        response = result.get('response', '')
        print(f"Response: {response[:200]}...")
    else:
        print(f"Error: {result.get('error')}")
    
    # Test 2: Saludo MCP
    print("\n📌 Test 2: Saludo MCP")
    result = run_orquestador("say_hello(name=Carlos, lang=es)")
    if result.get('success'):
        print(f"Intent: {result.get('intent')}")
        print(f"Tool used: {result.get('tool_used')}")
        print(f"Response: {result.get('response')}")
    else:
        print(f"Error: {result.get('error')}")
    
    # Test 3: Consulta general
    print("\n📌 Test 3: Consulta general")
    result = run_orquestador("Hola, ¿cómo estás?")
    if result.get('success'):
        print(f"Intent: {result.get('intent')}")
        print(f"Tool used: {result.get('tool_used')}")
        print(f"Response: {result.get('response')}")
    else:
        print(f"Error: {result.get('error')}")
    
    # Test 4: Clima sin ubicación
    print("\n📌 Test 4: Clima sin ubicación específica")
    result = run_orquestador("¿Qué tiempo hace hoy?")
    if result.get('success'):
        print(f"Intent: {result.get('intent')}")
        print(f"Tool used: {result.get('tool_used')}")
        print(f"Response: {result.get('response')}")
    else:
        print(f"Error: {result.get('error')}")
    
    # Test 5: Lista herramientas MCP
    print("\n📌 Test 5: Listar herramientas MCP")
    orquestador = AgentOrquestador()
    tools = orquestador.mcp_tool_names
    print(f"Herramientas MCP disponibles: {tools}")
    
    print("\n" + "=" * 60)
    print("✅ PRUEBAS COMPLETADAS")
    print("=" * 60)

except Exception as e:
    print(f"❌ Error en las pruebas: {e}")
    import traceback
    traceback.print_exc()
