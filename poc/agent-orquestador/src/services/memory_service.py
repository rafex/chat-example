"""
Servicio de memoria dual para el sistema de orquestación.

Implementa dos tipos de memoria:
1. Memoria corta conversacional: últimos turnos, contexto reciente
2. Memoria semántica con FAISS: recuperación de hechos relevantes
"""
import os
import json
import pickle
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


class ShortTermMemory:
    """Memoria corta conversacional para continuidad inmediata"""
    
    def __init__(self, max_turns: int = 10):
        """
        Args:
            max_turns: Número máximo de turnos a mantener en memoria
        """
        self.max_turns = max_turns
        self.conversation_history: List[Dict[str, Any]] = []
        self.session_id: Optional[str] = None
    
    def add_turn(self, role: str, content: str, metadata: Optional[Dict] = None):
        """Añade un turno a la memoria conversacional"""
        turn = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.conversation_history.append(turn)
        
        # Mantener solo los últimos N turnos
        if len(self.conversation_history) > self.max_turns:
            self.conversation_history = self.conversation_history[-self.max_turns:]
    
    def get_recent_history(self, n_turns: Optional[int] = None) -> List[Dict[str, Any]]:
        """Obtiene los últimos N turnos de la conversación"""
        if n_turns is None:
            n_turns = self.max_turns
        return self.conversation_history[-n_turns:]
    
    def get_full_context(self) -> str:
        """Convierte el historial a formato de texto para el LLM"""
        context_parts = []
        for turn in self.conversation_history:
            role = "Usuario" if turn["role"] == "user" else "Asistente"
            context_parts.append(f"{role}: {turn['content']}")
        return "\n".join(context_parts)
    
    def clear(self):
        """Limpia la memoria conversacional"""
        self.conversation_history = []


class SemanticMemory:
    """Memoria semántica con FAISS para recuperación de información relevante"""
    
    def __init__(self, dimension: int = 384, index_path: Optional[str] = None):
        """
        Args:
            dimension: Dimensión de los embeddings
            index_path: Ruta para guardar/cargar el índice FAISS
        """
        self.dimension = dimension
        self.index_path = index_path
        
        if not FAISS_AVAILABLE:
            raise ImportError("FAISS no está disponible. Instala faiss-cpu.")
        
        # Inicializar índice FAISS
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product (similaridad coseno)
        
        # Metadata asociada a cada embedding
        self.metadata: List[Dict[str, Any]] = []
        
        # Cargar índice si existe
        if index_path and os.path.exists(index_path):
            self.load()
    
    def add_memory(self, text: str, embedding: List[float], metadata: Optional[Dict] = None):
        """Añade un elemento a la memoria semántica"""
        # Convertir embedding a array de numpy
        embedding_array = np.array([embedding], dtype=np.float32)
        
        # Normalizar embedding para similitud coseno
        faiss.normalize_L2(embedding_array)
        
        # Añadir al índice
        self.index.add(embedding_array)
        
        # Guardar metadata
        self.metadata.append({
            "text": text,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "index_id": len(self.metadata)
        })
    
    def retrieve(self, query_embedding: List[float], k: int = 5) -> List[Dict[str, Any]]:
        """
        Recupera los k elementos más relevantes
        
        Returns:
            Lista de diccionarios con 'text', 'score' y 'metadata'
        """
        # Convertir query a array de numpy
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)
        
        # Buscar en el índice
        distances, indices = self.index.search(query_array, k)
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx >= 0 and idx < len(self.metadata):
                results.append({
                    "text": self.metadata[idx]["text"],
                    "score": float(dist),
                    "metadata": self.metadata[idx]["metadata"],
                    "timestamp": self.metadata[idx]["timestamp"]
                })
        
        return results
    
    def save(self):
        """Guarda el índice y metadata en disco"""
        if self.index_path:
            # Guardar índice FAISS
            faiss.write_index(self.index, self.index_path)
            
            # Guardar metadata
            metadata_path = self.index_path + ".meta"
            with open(metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
    
    def load(self):
        """Carga el índice y metadata desde disco"""
        if self.index_path and os.path.exists(self.index_path):
            # Cargar índice FAISS
            self.index = faiss.read_index(self.index_path)
            
            # Cargar metadata
            metadata_path = self.index_path + ".meta"
            if os.path.exists(metadata_path):
                with open(metadata_path, 'rb') as f:
                    self.metadata = pickle.load(f)
    
    def clear(self):
        """Limpia la memoria semántica"""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.metadata = []


class MemoryService:
    """Servicio principal que gestiona ambas memorias"""
    
    def __init__(self, session_id: str, semantic_index_path: Optional[str] = None):
        """
        Args:
            session_id: Identificador de sesión único
            semantic_index_path: Ruta para el índice FAISS
        """
        self.session_id = session_id
        self.short_term = ShortTermMemory()
        self.short_term.session_id = session_id
        
        # Configurar ruta para índice FAISS
        if semantic_index_path is None:
            memory_dir = Path.home() / ".agentes-langgraph" / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            semantic_index_path = str(memory_dir / f"session_{session_id}.faiss")
        
        # Inicializar memoria semántica
        try:
            self.semantic = SemanticMemory(index_path=semantic_index_path)
        except ImportError:
            # Fallback si FAISS no está disponible
            print("⚠️  FAISS no disponible, memoria semántica deshabilitada")
            self.semantic = None
    
    def add_conversation_turn(self, role: str, content: str):
        """Añade un turno a la memoria conversacional"""
        self.short_term.add_turn(role, content, {"session_id": self.session_id})
    
    def add_semantic_memory(self, text: str, embedding: List[float], metadata: Optional[Dict] = None):
        """Añade un elemento a la memoria semántica"""
        if self.semantic:
            full_metadata = metadata or {}
            full_metadata["session_id"] = self.session_id
            self.semantic.add_memory(text, embedding, full_metadata)
    
    def get_context(self, query_embedding: Optional[List[float]] = None, 
                   k_semantic: int = 3) -> Dict[str, Any]:
        """
        Obtiene el contexto completo para el LLM
        
        Returns:
            Diccionario con 'short_term' (historial) y 'semantic' (memoria recuperada)
        """
        context = {
            "short_term": self.short_term.get_recent_history(),
            "semantic": []
        }
        
        # Recuperar memoria semántica si hay query embedding
        if self.semantic and query_embedding is not None:
            context["semantic"] = self.semantic.retrieve(query_embedding, k=k_semantic)
        
        return context
    
    def get_formatted_context(self, query_embedding: Optional[List[float]] = None,
                            k_semantic: int = 3) -> str:
        """
        Obtiene el contexto formateado para el LLM
        """
        context = self.get_context(query_embedding, k_semantic)
        
        parts = []
        
        # Memoria conversacional
        if context["short_term"]:
            parts.append("=== Historial Reciente ===")
            for turn in context["short_term"]:
                role = "Usuario" if turn["role"] == "user" else "Asistente"
                parts.append(f"{role}: {turn['content']}")
        
        # Memoria semántica
        if context["semantic"]:
            parts.append("\n=== Memoria Semántica Relevante ===")
            for i, mem in enumerate(context["semantic"], 1):
                score_text = f"(similitud: {mem['score']:.3f})"
                parts.append(f"{i}. {mem['text']} {score_text}")
        
        return "\n".join(parts) if parts else "(sin contexto)"
    
    def save(self):
        """Guarda ambas memorias en disco"""
        if self.semantic:
            self.semantic.save()
    
    def clear_all(self):
        """Limpia todas las memorias"""
        self.short_term.clear()
        if self.semantic:
            self.semantic.clear()


# Instancia global para uso fácil
_memory_services: Dict[str, MemoryService] = {}


def get_memory_service(session_id: str = "default") -> MemoryService:
    """
    Obtiene la instancia global del servicio de memoria para una sesión
    
    Args:
        session_id: Identificador de sesión
        
    Returns:
        Instancia singleton del MemoryService
    """
    if session_id not in _memory_services:
        _memory_services[session_id] = MemoryService(session_id)
    return _memory_services[session_id]


def clear_memory_cache():
    """Limpia todas las instancias de memoria"""
    global _memory_services
    _memory_services = {}
