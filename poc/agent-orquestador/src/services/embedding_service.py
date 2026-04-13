"""
Servicio de embeddings con soporte para SentenceTransformers y TF-IDF como fallback.

Implementación de la DECISION-001 del proyecto:
- Backend principal: SentenceTransformers (mejor calidad de embeddings)
- Backend fallback: TF-IDF (si SentenceTransformers no está disponible)
- Dimensión fija: 384 (all-MiniLM-L6-v2) para consistencia
"""
import os
from typing import List, Optional, Union

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class EmbeddingService:
    """Servicio de embeddings con SentenceTransformers como backend principal"""
    
    def __init__(self, backend: str = "auto", model_name: str = "all-MiniLM-L6-v2"):
        """
        Args:
            backend: "auto" (detectar automáticamente), "transformers" (SentenceTransformers), "tfidf" (TF-IDF)
            model_name: Nombre del modelo para SentenceTransformers (default: all-MiniLM-L6-v2)
        """
        self.backend_type = backend
        self._backend = None
        self._model_name = model_name
        
        # Configurar backend
        if backend == "auto":
            self._detect_backend()
        elif backend == "transformers":
            self._setup_sentence_transformers()
        elif backend == "tfidf":
            self._setup_tfidf()
        else:
            raise ValueError(f"Backend '{backend}' no reconocido. Usar 'auto', 'transformers' o 'tfidf'.")
    
    def _detect_backend(self):
        """Detecta y configura el backend disponible"""
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self._setup_sentence_transformers()
                print(f"✅ Embeddings con SentenceTransformers (modelo: {self._model_name})")
            except Exception as e:
                print(f"⚠️  Error con SentenceTransformers: {e}")
                self._setup_tfidf()
                print("✅ Embeddings con TF-IDF (fallback)")
        else:
            print("⚠️  SentenceTransformers no disponible, usando TF-IDF")
            self._setup_tfidf()
    
    def _setup_sentence_transformers(self):
        """Configura el backend SentenceTransformers"""
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            self._dimension = 384  # all-MiniLM-L6-v2 genera embeddings de 384 dimensiones
        except Exception as e:
            print(f"Error al inicializar SentenceTransformers: {e}")
            raise
    
    def _setup_tfidf(self):
        """Configura el backend TF-IDF como fallback"""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vectorizer = TfidfVectorizer()
            self._dimension = None
            self._fit = False
            self._vocabulary = {}
        except ImportError:
            raise ImportError(
                "TF-IDF backend requiere scikit-learn. "
                "Instala las dependencias del proyecto con: pip install -e ."
            )
    
    def embed(self, texts: Union[str, List[str]]) -> List[List[float]]:
        """
        Genera embeddings para uno o más textos
        
        Args:
            texts: Texto individual o lista de textos
            
        Returns:
            Lista de embeddings (cada embedding es una lista de floats)
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return []
        
        # Verificar qué backend está activo
        if self.backend_type == "transformers" or (self.backend_type == "auto" and hasattr(self, '_model')):
            # Usar SentenceTransformers
            embeddings = self._model.encode(texts, show_progress_bar=False)
            return [emb.tolist() for emb in embeddings]
        
        elif self.backend_type == "tfidf" or (self.backend_type == "auto" and hasattr(self, '_vectorizer')):
            # Usar TF-IDF
            # Inicializar vectorizador si es la primera vez
            if not self._fit:
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
        
        else:
            raise ValueError("Backend no configurado correctamente")
    
    def embed_single(self, text: str) -> List[float]:
        """Genera embedding para un solo texto"""
        embeddings = self.embed([text])
        return embeddings[0] if embeddings else []
    
    @property
    def dimension(self) -> int:
        """Dimensión de los embeddings generados"""
        return self._dimension
    
    @property
    def backend_name(self) -> str:
        """Nombre del backend actualmente en uso"""
        if hasattr(self, '_model'):
            return "sentence-transformers"
        elif hasattr(self, '_vectorizer'):
            return "tfidf"
        else:
            return "unknown"


# Instancia global para uso fácil
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service(backend: str = "transformers", model_name: str = "all-MiniLM-L6-v2") -> EmbeddingService:
    """
    Obtiene la instancia global del servicio de embeddings
    
    Args:
        backend: Backend a usar ("transformers", "auto", "tfidf")
        model_name: Nombre del modelo para SentenceTransformers
        
    Returns:
        Instancia singleton del EmbeddingService
    """
    global _embedding_service
    
    if _embedding_service is None:
        _embedding_service = EmbeddingService(backend=backend, model_name=model_name)
    elif _embedding_service.backend_type != backend:
        # Si se solicita un backend diferente, reiniciar
        _embedding_service = EmbeddingService(backend=backend, model_name=model_name)
    
    return _embedding_service


def clear_embedding_cache():
    """Limpia la instancia global (útil para tests)"""
    global _embedding_service
    _embedding_service = None
