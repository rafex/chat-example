"""
Servicio de LLM ligero para Chat CLI.

Usa OpenRouter/gpt-oss-20b como modelo ligero para respuestas conversacionales.
"""
import os
import httpx
from typing import Dict, Any, Optional, List


class LLMLightService:
    """Servicio de LLM ligero usando OpenRouter"""
    
    def __init__(self, model: str = "openai/gpt-oss-20b:free"):
        """
        Args:
            model: Modelo a usar (default: openai/gpt-oss-20b:free)
        """
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        
        if not self.api_key:
            print("⚠️  OPENROUTER_API_KEY no encontrada en variables de entorno")
    
    def generate_response(self, messages: List[Dict[str, str]], max_tokens: int = 500) -> Dict[str, Any]:
        """
        Genera una respuesta usando el modelo ligero de OpenRouter
        
        Args:
            messages: Lista de mensajes en formato {"role": "user/assistant", "content": "..."}
            max_tokens: Máximo de tokens en la respuesta
            
        Returns:
            Diccionario con la respuesta y metadatos
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "API key de OpenRouter no configurada",
                "response": ""
            }
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            url = f"{self.base_url}/chat/completions"
            
            response = httpx.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                content = result["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "response": content,
                    "model": self.model,
                    "usage": result.get("usage", {})
                }
            else:
                return {
                    "success": False,
                    "error": "Respuesta inválida del modelo",
                    "response": ""
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": ""
            }


# Instancia global
_llm_service: Optional[LLMLightService] = None


def get_llm_service() -> LLMLightService:
    """Obtiene la instancia singleton del servicio de LLM ligero"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMLightService()
    return _llm_service


def generate_light_response(user_message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Genera una respuesta ligera para el chat
    
    Args:
        user_message: Mensaje del usuario
        conversation_history: Historial de la conversación
        
    Returns:
        Diccionario con la respuesta
    """
    service = get_llm_service()
    
    # Construir mensajes
    messages = []
    
    # Añadir historial si existe
    if conversation_history:
        for msg in conversation_history:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
    
    # Añadir mensaje actual
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    return service.generate_response(messages)
