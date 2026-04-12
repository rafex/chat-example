#!/usr/bin/env python3
"""
Chat CLI Interactivo Genérico con Herramientas y Memoria Temporal (FAISS)

Este chat permite:
1. Conversación general con el LLM
2. Consultas de clima usando la herramienta get_weather
3. Memoria temporal de conversación usando FAISS (mientras la sesión está abierta)
"""

import sys
import os
import uuid
import json
import numpy as np
import faiss
import re
from collections import Counter
from sentence_transformers import SentenceTransformer

# Configurar paths para importar desde poc/agent-weather y lib/mcp
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
agent_weather_path = os.path.join(project_root, 'poc', 'agent-weather')
lib_path = os.path.join(project_root, 'lib')
sys.path.insert(0, agent_weather_path)
sys.path.insert(0, lib_path)

# Importar desde poc/agent-weather
from src.schemas.chat import ChatSession, MessageType, Message
from src.services.generic_chat_service import GenericChatService  # Mantener como fallback

# Importar agente orquestador
# chat_cli.py está en: poc/chatCLI/src/chat_cli.py
# Project root es: agentes-con-LangGraph (3 niveles arriba de src)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
orquestador_src = os.path.join(project_root, 'poc', 'agent-orquestador', 'src')
agent_weather_src = os.path.join(project_root, 'poc', 'agent-weather', 'src')

# Añadir paths del agente orquestador
sys.path.insert(0, orquestador_src)
sys.path.insert(0, os.path.join(orquestador_src, 'agents'))
sys.path.insert(0, os.path.join(orquestador_src, 'schemas'))
sys.path.insert(0, os.path.join(orquestador_src, 'services'))
sys.path.insert(0, agent_weather_src)
sys.path.insert(0, os.path.join(agent_weather_src, 'services'))
sys.path.insert(0, os.path.join(agent_weather_src, 'schemas'))

try:
    from orquestador_agent import run_orquestador
    ORQUESTADOR_AVAILABLE = True
    print("✅ Agente orquestador importado exitosamente")
except ImportError as e:
    ORQUESTADOR_AVAILABLE = False
    print(f"⚠️  Agente orquestador no disponible: {e}")
    try:
        from src.agents.weather_agent import run_weather_agent
        print("✅ Usando agente meteorológico directo")
    except ImportError as e2:
        print(f"❌ Error importando agente meteorológico: {e2}")

# Importar MCP Router
from mcp.router import MCPRouter


class MemoryManager:
    """Gestor de memoria temporal usando FAISS con embeddings preentrenados"""
    
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        # Cargar modelo de embeddings preentrenado (ligero y eficiente)
        try:
            self.encoder = SentenceTransformer(model_name)
            self.dimension = self.encoder.get_sentence_embedding_dimension()
            print(f"🧠 Memoria temporal inicializada con FAISS (Embeddings: {model_name}, dim={self.dimension})")
        except Exception as e:
            print(f"⚠️  Error cargando modelo de embeddings: {e}")
            print("   Usando TF-IDF manual como fallback")
            self.encoder = None
            self.dimension = 256
        
        # Crear índice FAISS en memoria (no se guarda en disco)
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Almacenar textos y vectores
        self.texts = []
        self.vectors = []
        
        # Contador de palabras para estadísticas (opcional)
        self.word_counter = Counter()
    
    def _text_to_vector(self, text: str):
        """Convertir texto a vector de embeddings"""
        if self.encoder:
            # Usar modelo preentrenado para generar embeddings semánticos
            try:
                embedding = self.encoder.encode(text, convert_to_tensor=False)
                return embedding
            except Exception as e:
                print(f"⚠️  Error generando embedding: {e}")
        
        # Fallback: TF-IDF manual si el encoder no está disponible
        # Vocabulario común (stop words básicas en español/inglés)
        stop_words = set([
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            'de', 'del', 'al', 'en', 'con', 'por', 'para', 'sobre',
            'y', 'o', 'pero', 'porque', 'que', 'como', 'cuando',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are'
        ])
        
        # Tokenizar texto
        words = re.findall(r'\w+', text.lower())
        
        # Filtrar stop words
        words = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Contar palabras
        word_counts = Counter(words)
        
        # Crear vector
        vector = np.zeros(self.dimension)
        
        # Asignar índices a palabras basado en frecuencia global
        for i, (word, count) in enumerate(word_counts.most_common(self.dimension)):
            if i < self.dimension:
                # Usar hash simple para mapear palabra a índice
                idx = hash(word) % self.dimension
                vector[idx] = count
        
        return vector
    
    def add_message(self, text: str, role: str):
        """Agregar un mensaje a la memoria"""
        if not text.strip():
            return
        
        # Generar vector
        vector = self._text_to_vector(text)
        
        # Agregar al índice FAISS
        self.index.add(np.array([vector], dtype=np.float32))
        
        # Guardar texto con metadata
        self.texts.append({
            'text': text,
            'role': role
        })
        
        # Actualizar contador de palabras
        words = re.findall(r'\w+', text.lower())
        self.word_counter.update(words)
    
    def search(self, query: str, k: int = 3):
        """Buscar mensajes similares a la consulta"""
        if len(self.texts) == 0:
            return []
        
        # Generar vector de la consulta
        query_vector = self._text_to_vector(query)
        
        # Buscar en FAISS
        distances, indices = self.index.search(
            np.array([query_vector], dtype=np.float32), 
            min(k, len(self.texts))
        )
        
        # Recuperar textos similares
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.texts):
                results.append({
                    'text': self.texts[idx]['text'],
                    'role': self.texts[idx]['role'],
                    'distance': distances[0][i]
                })
        
        return results
    
    def clear(self):
        """Limpiar toda la memoria"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.texts = []
        self.vectors = []
        self.word_counter = Counter()
        print("🧠 Memoria temporal limpiada")


def clear_screen():
    """Limpiar la pantalla"""
    os.system('clear' if os.name == 'posix' else 'cls')


def print_banner():
    """Mostrar banner del chat"""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║              🤖  CHAT CONVERSACIONAL CON HERRAMIENTAS  🧠            ║
║                                                                      ║
║  Asistente conversacional con capacidad de consultar el clima       ║
║  y responder a cualquier consulta general                           ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def format_message(msg):
    """Formatear mensaje para mostrar en consola"""
    timestamp = msg.timestamp.strftime("%H:%M:%S")

    if msg.type == MessageType.USER:
        return f"\n👤 TÚ [{timestamp}]: {msg.content}"
    elif msg.type == MessageType.ASSISTANT:
        return f"\n🤖 ASISTENTE [{timestamp}]:\n{msg.content}"
    elif msg.type == MessageType.SYSTEM:
        return f"\nℹ️  SISTEMA: {msg.content}"
    else:
        return f"\n{msg.content}"


def main():
    """Función principal del chat"""
    try:
        clear_screen()
        print_banner()

        # Inicializar sesión, servicio de chat, memoria temporal y router MCP
        session_id = str(uuid.uuid4())[:8]
        chat_session = ChatSession(id=session_id)
        chat_service = GenericChatService()
        memory = MemoryManager()
        mcp_router = MCPRouter()

        print(f"\n💡 Sesión iniciada: {session_id}")
        print("💡 Escribe 'salir' o 'exit' para terminar")
        print("💡 Escribe 'ayuda' para ver comandos disponibles")
        print("💡 Escribe 'herramientas' para ver herramientas disponibles")
        print("-" * 70)

        # Mensaje de bienvenida del asistente
        welcome_msg = Message(
            type=MessageType.ASSISTANT,
            content="🤖 ¡Hola! Soy tu asistente conversacional.\n"
                    "Puedo conversar sobre cualquier tema y también consultar el clima.\n"
                    "Mantengo memoria de nuestra conversación mientras estés aquí.\n"
                    "Prueba con:\n"
                    "• '¿Cómo estás?'\n"
                    "• '¿Cómo está el clima en Madrid?'\n"
                    "• 'Explícame el concepto de inteligencia artificial'\n\n"
                    "Escribe 'ayuda' para más información."
        )
        chat_session.add_message(welcome_msg.type, welcome_msg.content)
        print(format_message(welcome_msg))

        # Bucle principal del chat
        while True:
            try:
                # Leer entrada del usuario
                user_input = input("\n👤 Tu mensaje: ").strip()

                # Comandos especiales
                if user_input.lower() in ['salir', 'exit', 'quit', 'adiós']:
                    goodbye_msg = Message(
                        type=MessageType.ASSISTANT,
                        content="👋 ¡Hasta pronto! Que tengas un buen día."
                    )
                    chat_session.add_message(goodbye_msg.type, goodbye_msg.content)
                    print(format_message(goodbye_msg))
                    memory.clear()  # Limpiar memoria al salir
                    break

                if user_input.lower() in ['limpiar', 'clear', 'cls']:
                    clear_screen()
                    print_banner()
                    print("\n💡 Pantalla limpiada.")
                    continue

                if user_input.lower() in ['historial', 'history']:
                    print("\n📜 Historial de la sesión:")
                    for msg in chat_session.messages[-5:]:
                        print(format_message(msg))
                    continue

                if user_input.lower() in ['herramientas', 'tools']:
                    print("\n🔧 HERRAMIENTAS DISPONIBLES:")
                    print("• get_weather(location): Consulta el clima de una ciudad")
                    print("• say_hello(name, lang): Saludo personalizado en diferentes idiomas")
                    print("• get_hello_languages(): Obtener idiomas soportados")
                    continue
                
                # Comandos MCP directos
                if user_input.lower().startswith('mcp '):
                    # Ejecutar comando MCP directo
                    try:
                        command = user_input[4:].strip()
                        if command == 'list-tools':
                            request = {"method": "tools/list", "id": 1}
                            response = mcp_router.handle_request(request)
                            if response and 'result' in response:
                                tools = response['result'].get('tools', [])
                                print("\n🔧 Herramientas MCP disponibles:")
                                for tool in tools:
                                    print(f"• {tool['name']}: {tool.get('description', 'Sin descripción')}")
                        else:
                            print("Comando MCP no reconocido. Usa 'mcp list-tools' para ver herramientas disponibles.")
                    except Exception as e:
                        print(f"Error ejecutando comando MCP: {e}")
                    continue

                if user_input == '':
                    continue

                # Detectar y ejecutar comandos MCP
                if user_input.strip().startswith('say_hello(') or user_input.strip().startswith('get_hello_languages('):
                    try:
                        # Parsear el comando MCP
                        command = user_input.strip()
                        if command.startswith('say_hello('):
                            # Extraer parámetros
                            params_str = command[10:-1]  # Remover 'say_hello(' y ')'
                            params = {}
                            for part in params_str.split(','):
                                if '=' in part:
                                    key, value = part.split('=', 1)
                                    params[key.strip()] = value.strip().strip("'\"")
                        
                            # Ejecutar herramienta MCP
                            request = {
                                "method": "tools/call",
                                "id": 1,
                                "params": {
                                    "name": "say_hello",
                                    "arguments": params
                                }
                            }
                            response = mcp_router.handle_request(request)
                            
                            if response and 'result' in response:
                                content = response['result']['content'][0]['text']
                                result_data = json.loads(content)
                                message = result_data.get('message', 'Saludo ejecutado')
                                
                                # Mostrar resultado
                                print(f"\n🔧 Resultado MCP: {message}")
                                
                                # Agregar al historial
                                assistant_msg = Message(
                                    type=MessageType.ASSISTANT,
                                    content=message
                                )
                                chat_session.add_message(MessageType.USER, user_input)
                                chat_session.add_message(assistant_msg.type, assistant_msg.content)
                                memory.add_message(message, 'assistant')
                                print(format_message(assistant_msg))
                                continue
                    except Exception as e:
                        print(f"\n❌ Error ejecutando comando MCP: {e}")
                        continue

                # Agregar mensaje del usuario a la memoria
                memory.add_message(user_input, 'user')

                # Buscar contexto relevante en la memoria
                context_results = memory.search(user_input)
                context_text = ""
                if context_results:
                    context_text = "\n".join([f"- {r['text']}" for r in context_results])
                    print(f"\n🧠 Contexto recuperado de la memoria:\n{context_text}")

                # Usar agente orquestador si está disponible
                if ORQUESTADOR_AVAILABLE:
                    try:
                        # Preparar historial para el agente orquestador
                        conversation_history = [
                            {"role": msg.type.value, "content": msg.content}
                            for msg in chat_session.messages
                        ]
                        
                        # Ejecutar agente orquestador
                        orquestador_result = run_orquestador(user_input, conversation_history)
                        
                        if orquestador_result['success']:
                            response_text = orquestador_result['response']
                            print(f"\n🧠 Agente orquestador: {orquestador_result['tool_used']} -> {orquestador_result['intent']}")
                        else:
                            response_text = orquestador_result['response']
                            print(f"\n⚠️ Error en agente orquestador, usando fallback: {orquestador_result.get('error')}")
                    except Exception as e:
                        print(f"\n⚠️ Error ejecutando agente orquestador: {e}")
                        # Fallback a chat genérico
                        conversation_history = [
                            {"role": msg.type.value, "content": msg.content}
                            for msg in chat_session.messages
                        ]
                        conversation_history.append({"role": "user", "content": user_input})
                        result_chat = chat_service.chat(user_input, conversation_history)
                        response_text = result_chat['response']
                else:
                    # Fallback: usar lógica anterior
                    weather_keywords = ['clima', 'weather', 'temperatura', ' temperatura', 'lluvia', 'rain', 'sol', 'sun', 'viento', 'wind', 'humedad', 'humidity']
                    is_weather_query = any(keyword in user_input.lower() for keyword in weather_keywords)
                    
                    if is_weather_query:
                        # Extraer ubicación del mensaje
                        location = None
                        
                        # Patrones comunes para extraer ubicación
                        patterns = [
                            r'en\s+(\w+(?:\s+\w+)*?)\s*(?:\?|\.|$|,)',
                            r'en\s+(\w+(?:\s+\w+)*?)\s*$',
                            r'(\bMadrid\b|\bBarcelona\b|\bValencia\b|\bSevilla\b|\bBilbao\b|\bZaragoza\b|\bPalma\b|\bMurcia\b|\bGranada\b|\bAlicante\b)',
                        ]
                        
                        for pattern in patterns:
                            match = re.search(pattern, user_input, re.IGNORECASE)
                            if match:
                                location = match.group(1)
                                break
                        
                        if location:
                            print(f"\n🌤️ Consultando clima para: {location}")
                            try:
                                # Usar el agente meteorológico
                                weather_result = run_weather_agent(location)
                                
                                if weather_result['success']:
                                    analysis = weather_result['analysis']
                                    recommendations = weather_result['recommendations']
                                    
                                    # Construir respuesta
                                    response_text = f"🌞 Clima en {analysis['location']}:\n"
                                    response_text += f"   - Temperatura: {analysis['temperature_celsius']}°C ({analysis['temperature']}°F)\n"
                                    response_text += f"   - Condición: {analysis['condition']}\n"
                                    response_text += f"   - Humedad: {analysis['humidity']}%\n"
                                    response_text += f"   - Viento: {analysis['wind_speed']} m/s\n\n"
                                    response_text += "💡 Recomendaciones:\n"
                                    for rec in recommendations:
                                        response_text += f"   - {rec}\n"
                                else:
                                    response_text = f"❌ No pude obtener el clima para {location}. Error: {weather_result.get('error', 'Desconocido')}"
                            except Exception as e:
                                response_text = f"❌ Error al consultar el clima: {str(e)}"
                        else:
                            # No se encontró ubicación, usar chat genérico
                            conversation_history = [
                                {"role": msg.type.value, "content": msg.content}
                                for msg in chat_session.messages
                            ]
                            conversation_history.append({"role": "user", "content": user_input})
                            result_chat = chat_service.chat(user_input, conversation_history)
                            response_text = result_chat['response']
                    else:
                        # No es consulta de clima, usar chat genérico
                        conversation_history = [
                            {"role": msg.type.value, "content": msg.content}
                            for msg in chat_session.messages
                        ]
                        conversation_history.append({"role": "user", "content": user_input})
                        result_chat = chat_service.chat(user_input, conversation_history)
                        response_text = result_chat['response']

                # Crear mensaje del asistente
                assistant_msg = Message(
                    type=MessageType.ASSISTANT,
                    content=response_text
                )

                # Guardar en el historial
                chat_session.add_message(MessageType.USER, user_input)
                chat_session.add_message(assistant_msg.type, assistant_msg.content)

                # Agregar respuesta del asistente a la memoria
                memory.add_message(response_text, 'assistant')

                # Mostrar respuesta
                print(format_message(assistant_msg))

            except KeyboardInterrupt:
                print("\n\n👋 Saliendo del chat...")
                memory.clear()
                break
            except Exception as e:
                error_msg = Message(
                    type=MessageType.SYSTEM,
                    content=f"❌ Error: {str(e)}"
                )
                chat_session.add_message(error_msg.type, error_msg.content)
                print(format_message(error_msg))

    except Exception as e:
        print(f"\n❌ Error al iniciar el chat: {e}")
        print("\nVerifica que:")
        print("1. El entorno virtual esté activado")
        print("2. Las dependencias estén instaladas")
        print("3. Las API keys estén configuradas en .env")
        sys.exit(1)


if __name__ == "__main__":
    main()
