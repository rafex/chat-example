"""
Servicio de embeddings usando exclusivamente TF-IDF manual

Nota: Este servicio implementa la DECISION-001 del proyecto:
"Uso de TF-IDF Manual en lugar de SentenceTransformers"

El sistema NO usa SentenceTransformers para mantener la simplicidad
y evitar dependencias externas adicionales.
"""
import os
from typing import List, Optional, Union


class EmbeddingService:
    """Servicio de embeddings basado exclusivamente en TF-IDF manual"""
    
    def __init__(self, backend: str = "tfidf"):
        """
        Args:
            backend: Siempre "tfidf" (mantenido para compatibilidad)
        """
        if backend != "tfidf":
            raise ValueError(f"Backend '{backend}' no soportado. Usar 'tfidf' exclusivamente.")
        
        self.backend_type = backend
        self._vectorizer = None
        self._dimension = None
        self._fit = False
        self._vocabulary = {}
        
        # Intentar importar sklearn
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.TfidfVectorizer = TfidfVectorizer
        except ImportError:
            raise ImportError(
                "TF-IDF backend requiere scikit-learn. "
                "Instala las dependencias del proyecto con: pip install -e ."
            )
    
    def embed(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Genera embeddings usando TF-IDF
        
        Args:
            texts: Texto individual o lista de textos
            
        Returns:
            Lista de embeddings (cada embedding es una lista de floats)
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return []
        
        # Inicializar vectorizador si es la primera vez
        if not self._fit:
            self._vectorizer = self.TfidfVectorizer()
            self._vectorizer.fit(texts)
            self._fit = True
            self._dimension = len(self._vectorizer.vocabulary_)
            self._vocabulary = self._vectorizer.vocabulary_
        
        # Generar embeddings
        embeddings_sparse = self._vectorizer.transform(texts)
        
        # Convertir sparse matrix a lista de listas
        embeddings = []
        for i in range(embeddings_sparse.shape[0]):
            row = embeddings_sparse[i].toarray()[0]
            embeddings.append(row.tolist())
        
        return embeddings
    
    def embed_single(self, text: str) -> List[float]:
        """Genera embedding para un solo texto"""
        embeddings = self.embed([text])
        return embeddings[0] if embeddings else []
    
    @property
    def dimension(self) -> int:
        """Dimensión de los embeddings generados"""
        if self._dimension is None:
            raise ValueError("TFIDF no ha sido ajustado aún. Llama a embed() primero.")
        return self._dimension
    
    @property
    def backend_name(self) -> str:
        """Nombre del backend actualmente en uso"""
        return self.backend_type
    
    @property
    def vocabulary_size(self) -> int:
        """Tamaño del vocabulario"""
        return len(self._vocabulary) if self._vocabulary else 0


# Instancia global para uso fácil
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(backend: str = "tfidf") -> EmbeddingService:
    """
    Obtiene la instancia global del servicio de embeddings
    
    Args:
        backend: Backend a usar ("tfidf" - único soportado)
        
    Returns:
        Instancia singleton del EmbeddingService
    """
    global _embedding_service
    
    # Forzar backend a 'tfidf' para mantener DECISION-001
    backend = "tfidf"
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService(backend=backend)
    elif _embedding_service.backend_type != backend:
        # Si se solicita un backend diferente, reiniciar
        _embedding_service = EmbeddingService(backend=backend)
    
    return _embedding_service


def clear_embedding_cache():
    """Limpia la instancia global (útil para tests)"""
    global _embedding_service
    _embedding_service = None
