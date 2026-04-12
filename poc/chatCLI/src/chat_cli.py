#!/usr/bin/env python3
"""
Chat CLI Interactivo Genérico con Herramientas y Memoria Temporal (FAISS)
"""

import sys
import os
import uuid
import json
import re
from collections import Counter

# Sentencias try/except para importaciones opcionales
try:
    import numpy as np
except ImportError:
    print("⚠️  numpy no disponible, algunas funcionalidades pueden fallar")
    np = None

try:
    import faiss
except ImportError:
    print("⚠️  faiss no disponible, memoria FAISS no funcionará")
    faiss = None

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  SentenceTransformers no disponible: {e}")
    print("   Usando TF-IDF manual como fallback")
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# ==============================================================================
# CONFIGURACIÓN DE PATHS
# ==============================================================================

# El directorio donde está este archivo
current_dir = os.path.dirname(os.path.abspath(__file__))

# Añadir el directorio src de chatCLI al path (esto permite importar desde agents, schemas, etc.)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Configurar paths para importar desde poc/agent-weather y lib/mcp
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
agent_weather_src = os.path.join(project_root, 'poc', 'agent-weather', 'src')
lib_path = os.path.join(project_root, 'lib')

if agent_weather_src not in sys.path:
    sys.path.insert(0, agent_weather_src)
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

# ==============================================================================
# IMPORTACIONES DESDE AGENT-WEATHER
# ==============================================================================
try:
    from src.schemas.chat import ChatSession, MessageType, Message
    from src.services.generic_chat_service import GenericChatService
    from src.config import Config
    print("✅ Importaciones de agent-weather exitosas")
except ImportError as e:
    print(f"⚠️  Error importando agent-weather: {e}")
    # Crear clases básicas como fallback
    class MessageType:
        USER = "user"
        ASSISTANT = "assistant"
        SYSTEM = "system"
    
    class Message:
        def __init__(self, type, content):
            self.type = type
            self.content = content
            self.timestamp = None
    
    class ChatSession:
        def __init__(self, id):
            self.id = id
            self.messages = []
        
        def add_message(self, msg_type, content):
            self.messages.append(Message(msg_type, content))

# ==============================================================================
# IMPORTACIÓN DEL AGENTE ORQUESTADOR
# ==============================================================================

# Importar desde el directorio src de chatCLI (donde están los módulos copiados)
try:
    from agents.orquestador_agent import run_orquestador, tool_registry
    ORQUESTADOR_AVAILABLE = True
    print("✅ Agente orquestador importado exitosamente")
    print(f"   Herramientas disponibles: {len(tool_registry.list_tools())}")
except ImportError as e:
    ORQUESTADOR_AVAILABLE = False
    print(f"⚠️  Agente orquestador no disponible: {e}")
    
    # Intentar fallback a agente meteorológico directo
    try:
        from src.agents.weather_agent import run_weather_agent
        print("✅ Usando agente meteorológico directo")
    except ImportError as e2:
        print(f"⚠️  Error importando agente meteorológico: {e2}")
        run_weather_agent = None

# Importar MCP Router
try:
    from mcp.router import MCPRouter
    MCP_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  MCP Router no disponible: {e}")
    MCP_AVAILABLE = False
    MCPRouter = None

# ==============================================================================
# CÓDIGO PRINCIPAL DEL CHAT
# ==============================================================================

class MemoryManager:
    """Gestor de memoria temporal usando FAISS con embeddings preentrenados"""
    
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        # Cargar modelo de embeddings preentrenado (ligero y eficiente)
        if SENTENCE_TRANSFORMERS_AVAILABLE and SentenceTransformer is not None:
            try:
                self.encoder = SentenceTransformer(model_name)
                self.dimension = self.encoder.get_sentence_embedding_dimension()
                print(f"🧠 Memoria temporal inicializada con FAISS (Embeddings: {model_name}, dim={self.dimension})")
            except Exception as e:
                print(f"⚠️  Error cargando modelo de embeddings: {e}")
                print("   Usando TF-IDF manual como fallback")
                self.encoder = None
                self.dimension = 256
        else:
            print("🧠 Usando TF-IDF manual (SentenceTransformers no disponible)")
            self.encoder = None
            self.dimension = 256
        
        # Crear índice FAISS en memoria (no se guarda en disco)
        if faiss is not None:
            self.index = faiss.IndexFlatL2(self.dimension)
        else:
            self.index = None
        
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
        if np is not None:
            vector = np.zeros(self.dimension)
            
            # Asignar índices a palabras basado en frecuencia global
            for i, (word, count) in enumerate(word_counts.most_common(self.dimension)):
                if i < self.dimension:
                    # Usar hash simple para mapear palabra a índice
                    idx = hash(word) % self.dimension
                    vector[idx] = count
        else:
            # Fallback si numpy no está disponible
            vector = [0] * self.dimension
        
        return vector
    
    def add_message(self, text: str, role: str):
        """Agregar un mensaje a la memoria"""
        if not text.strip():
            return
        
        # Generar vector
        vector = self._text_to_vector(text)
        
        # Agregar al índice FAISS
        if self.index is not None and np is not None:
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
        if len(self.texts) == 0 or self.index is None or np is None:
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
        if faiss is not None:
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
    if hasattr(msg, 'timestamp') and msg.timestamp:
        timestamp = msg.timestamp.strftime("%H:%M:%S")
    else:
        timestamp = ""
    
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
        
        # Inicializar memoria (manejar caso donde FAISS no esté disponible)
        if faiss is not None:
            memory = MemoryManager()
        else:
            print("⚠️  FAISS no disponible, memoria semántica deshabilitada")
            memory = None
        
        # Inicializar MCP router si está disponible
        mcp_router = None
        if MCP_AVAILABLE and MCPRouter is not None:
            try:
                mcp_router = MCPRouter()
                print(f"✅ Servidor MCP inicializado")
            except Exception as e:
                print(f"⚠️  Error inicializando MCP: {e}")
                mcp_router = None

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
                    if memory:
                        memory.clear()
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
                    if ORQUESTADOR_AVAILABLE:
                        for tool in tool_registry.list_tools():
                            print(f"• {tool.name}: {tool.description}")
                    else:
                        print("• get_weather(location): Consulta el clima de una ciudad")
                    continue

                if user_input.lower() in ['ayuda', 'help']:
                    print("\n💡 COMANDOS DISPONIBLES:")
                    print("• /model [openai|deepseek|openrouter]: Cambiar proveedor LLM")
                    print("• mcp list-tools: Listar herramientas MCP disponibles")
                    print("• historial: Ver historial de la sesión")
                    print("• herramientas: Ver herramientas disponibles")
                    print("• limpiar: Limpiar pantalla")
                    print("• salir: Terminar la conversación")
                    continue

                # Comando para cambiar modelo LLM
                if user_input.lower().startswith('/model '):
                    provider = user_input[7:].strip().lower()
                    if provider in ['openai', 'deepseek', 'openrouter']:
                        try:
                            Config.set_provider(provider)
                            print(f"✅ Proveedor LLM cambiado a: {provider}")
                            print(f"   Modelo actual: {Config.get_current_config()['model']}")
                        except Exception as e:
                            print(f"❌ Error cambiando proveedor: {e}")
                    else:
                        print(f"❌Proveedor no reconocido: {provider}")
                        print("   Usar: /model openai, /model deepseek, o /model openrouter")
                    continue
                
                # Comandos MCP directos
                if user_input.lower().startswith('mcp '):
                    # Ejecutar comando MCP directo
                    try:
                        command = user_input[4:].strip()
                        if command == 'list-tools':
                            if mcp_router:
                                request = {"method": "tools/list", "id": 1}
                                response = mcp_router.handle_request(request)
                                if response and 'result' in response:
                                    tools = response['result'].get('tools', [])
                                    print("\n🔧 Herramientas MCP disponibles:")
                                    for tool in tools:
                                        print(f"• {tool['name']}: {tool.get('description', 'Sin descripción')}")
                            else:
                                print("❌ MCP Router no disponible")
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
                            if mcp_router:
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
                                    if memory:
                                        memory.add_message(message, 'assistant')
                                    print(format_message(assistant_msg))
                                    continue
                    except Exception as e:
                        print(f"\n❌ Error ejecutando comando MCP: {e}")
                        continue

                # Agregar mensaje del usuario a la memoria
                if memory:
                    memory.add_message(user_input, 'user')

                # Buscar contexto relevante en la memoria
                if memory:
                    context_results = memory.search(user_input)
                    context_text = ""
                    if context_results:
                        context_text = "\n".join([f"- {r['text']}" for r in context_results])
                        print(f"\n🧠 Contexto recuperado de la memoria:\n{context_text}")

                # Ejecutar agente orquestador (siempre disponible si el Chat CLI se ejecuta correctamente)
                if ORQUESTADOR_AVAILABLE:
                    try:
                        # Preparar historial para el agente orquestador
                        conversation_history = [
                            {"role": msg.type if isinstance(msg.type, str) else msg.type.value, "content": msg.content}
                            for msg in chat_session.messages
                        ]
                        
                        # Ejecutar agente orquestador
                        orquestador_result = run_orquestador(user_input, conversation_history)
                        
                        if orquestador_result['success']:
                            response_text = orquestador_result['response']
                            print(f"\n🧠 Agente orquestador: {orquestador_result['tool_used']} -> {orquestador_result['intent']}")
                        else:
                            response_text = orquestador_result['response']
                            print(f"\n⚠️ Error en agente orquestador: {orquestador_result.get('error')}")
                    except Exception as e:
                        response_text = f"❌ Error crítico en agente orquestador: {str(e)}"
                        print(f"\n{response_text}")
                else:
                    # Si el agente orquestador no está disponible, usar agente meteorológico directo
                    if run_weather_agent:
                        try:
                            result = run_weather_agent(user_input)
                            if result.get('success'):
                                analysis = result.get('analysis')
                                if analysis:
                                    response_text = f"🌞 Clima en {analysis['location']}:\n"
                                    response_text += f"   - Temperatura: {analysis.get('temperature_celsius', 'N/A')}°C\n"
                                    response_text += f"   - Condición: {analysis.get('condition', 'N/A')}\n"
                                    if 'recommendations' in result:
                                        response_text += "\n💡 Recomendaciones:\n"
                                        for rec in result['recommendations']:
                                            response_text += f"   - {rec}\n"
                                else:
                                    response_text = "No se pudo obtener el clima."
                            else:
                                response_text = "No tengo acceso a esa capacidad en esta versión."
                        except Exception as e:
                            response_text = f"❌ Error: {str(e)}"
                    else:
                        response_text = "❌ Agente orquestador no disponible. El Chat CLI requiere el agente orquestador para funcionar."
                    print(f"\n{response_text}")

                # Crear mensaje del asistente
                assistant_msg = Message(
                    type=MessageType.ASSISTANT,
                    content=response_text
                )

                # Guardar en el historial
                chat_session.add_message(MessageType.USER, user_input)
                chat_session.add_message(assistant_msg.type, assistant_msg.content)

                # Agregar respuesta del asistente a la memoria
                if memory:
                    memory.add_message(response_text, 'assistant')

                # Mostrar respuesta
                print(format_message(assistant_msg))

            except KeyboardInterrupt:
                print("\n\n👋 Saliendo del chat...")
                if memory:
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
