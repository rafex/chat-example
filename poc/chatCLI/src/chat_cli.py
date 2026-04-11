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
import numpy as np
import faiss
import re
from collections import Counter

# Configurar paths para importar desde poc/agent-weather
agent_weather_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'agent-weather')
sys.path.insert(0, agent_weather_path)

# Importar desde poc/agent-weather
from src.schemas.chat import ChatSession, MessageType, Message
from src.services.generic_chat_service import GenericChatService


class MemoryManager:
    """Gestor de memoria temporal usando FAISS con vectores TF-IDF manuales"""
    
    def __init__(self):
        self.dimension = 1000  # Tamaño del vocabulario (palabras más frecuentes)
        
        # Crear índice FAISS en memoria (no se guarda en disco)
        self.index = faiss.IndexFlatL2(self.dimension)
        
        # Almacenar textos y vectores
        self.texts = []
        self.vectors = []
        
        # Vocabulario común (stop words básicas en español/inglés)
        self.stop_words = set([
            'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
            'de', 'del', 'al', 'en', 'con', 'por', 'para', 'sobre',
            'y', 'o', 'pero', 'porque', 'que', 'como', 'cuando',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are'
        ])
        
        # Contador de palabras para construir vocabulario
        self.word_counter = Counter()
        
        print("🧠 Memoria temporal inicializada con FAISS (TF-IDF manual)")
    
    def _text_to_vector(self, text: str):
        """Convertir texto a vector TF-IDF manual"""
        # Tokenizar texto
        words = re.findall(r'\w+', text.lower())
        
        # Filtrar stop words
        words = [w for w in words if w not in self.stop_words and len(w) > 2]
        
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

        # Inicializar sesión, servicio de chat y memoria temporal
        session_id = str(uuid.uuid4())[:8]
        chat_session = ChatSession(id=session_id)
        chat_service = GenericChatService()
        memory = MemoryManager()

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
                    continue

                if user_input == '':
                    continue

                # Agregar mensaje del usuario a la memoria
                memory.add_message(user_input, 'user')

                # Buscar contexto relevante en la memoria
                context_results = memory.search(user_input)
                context_text = ""
                if context_results:
                    context_text = "\n".join([f"- {r['text']}" for r in context_results])
                    print(f"\n🧠 Contexto recuperado de la memoria:\n{context_text}")

                # Preparar historial para el servicio de chat
                conversation_history = [
                    {"role": msg.type.value, "content": msg.content}
                    for msg in chat_session.messages
                ]

                # Procesar mensaje con el servicio de chat
                result = chat_service.chat(user_input, conversation_history)

                # Mostrar indicador si se usó una herramienta
                if result.get('tool_used'):
                    print(f"\n🔧 Usando herramienta: {result['tool_used']} con {result['tool_args']}")

                # Crear mensaje del asistente
                assistant_msg = Message(
                    type=MessageType.ASSISTANT,
                    content=result['response']
                )

                # Guardar en el historial
                chat_session.add_message(MessageType.USER, user_input)
                chat_session.add_message(assistant_msg.type, assistant_msg.content, result)

                # Agregar respuesta del asistente a la memoria
                memory.add_message(result['response'], 'assistant')

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
