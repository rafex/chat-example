"""
Agente de Seguridad (Guard Agent)

Responsabilidad:
- Revisar respuestas de otros agentes por seguridad
- Detectar contenido inapropiado, sesgos, información personal
- Validar que las respuestas cumplan políticas de seguridad
- Usar modelo OpenAI GPT-OSS-Safeguard-20b vía OpenRouter
"""
import os
import json
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime


class GuardAgent:
    """Agente de seguridad para revisión de respuestas"""
    
    def __init__(self, provider: str = "openrouter", model: str = "openai/gpt-oss-safeguard-20b"):
        """
        Args:
            provider: Provider a usar (default: openrouter)
            model: Modelo a usar (default: openai/gpt-oss-safeguard-20b)
        """
        self.provider = provider
        self.model = model
        
        # Cargar configuración
        self._load_config()
    
    def _load_config(self):
        """Carga la configuración del provider"""
        # Obtener URL base del provider
        providers_config = {
            "openrouter": {
                "base_url": "https://openrouter.ai/api/v1",
                "api_key_env": "OPENROUTER_API_KEY"
            }
        }
        
        config = providers_config.get(self.provider, {})
        self.base_url = config.get("base_url", "")
        self.api_key = os.getenv(config.get("api_key_env", ""), "")
        
        if not self.api_key:
            print(f"⚠️  API key no encontrada para {self.provider}")
    
    def review_response(self, response_text: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Revisa una respuesta por seguridad
        
        Args:
            response_text: Texto a revisar
            context: Contexto opcional (mensaje del usuario, historial)
            
        Returns:
            Diccionario con resultado de la revisión
        """
        if not self.api_key:
            return {
                "safe": True,
                "review_id": "skipped",
                "reason": "API key no configurada",
                "details": {},
                "timestamp": datetime.now().isoformat()
            }
        
        # Construir prompt de seguridad
        prompt = self._build_security_prompt(response_text, context)
        
        # Llamar al modelo de seguridad
        try:
            result = self._call_safeguard_model(prompt)
            return result
        except Exception as e:
            print(f"⚠️  Error en revisión de seguridad: {e}")
            return {
                "safe": True,
                "review_id": "error",
                "reason": f"Error: {str(e)}",
                "details": {},
                "timestamp": datetime.now().isoformat()
            }
    
    def _build_security_prompt(self, response_text: str, context: Optional[str] = None) -> str:
        """Construye el prompt para el modelo de seguridad"""
        prompt = f"""Eres un agente de seguridad que revisa respuestas de asistentes de IA.

INSTRUCCIONES:
1. Analiza la respuesta en busca de contenido inapropiado
2. Detecta sesgos, información personal, contenido violento, etc.
3. Devuelve un resultado JSON estructurado

RESPUESTA A REVISAR:
{response_text}

CONTEXT (opcional):
{context or "Sin contexto"}

ANALIZA Y DEVUELVE JSON CON:
{{
  "safe": true/false,
  "issues": [lista de problemas detectados],
  "severity": "low/medium/high",
  "recommendations": [sugerencias de mejora],
  "reason": "explicación breve"
}}"""
        return prompt
    
    def _call_safeguard_model(self, prompt: str) -> Dict[str, Any]:
        """Llama al modelo de seguridad de OpenRouter"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Eres un agente de seguridad de IA. Solo devuelves JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 500,
            "temperature": 0.1
        }
        
        url = f"{self.base_url}/chat/completions"
        
        response = httpx.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        
        # Parsear respuesta del modelo
        content = result["choices"][0]["message"]["content"]
        
        # Intentar extraer JSON del contenido
        try:
            # Buscar bloque JSON en la respuesta
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            else:
                json_str = content
            
            safety_result = json.loads(json_str)
        except json.JSONDecodeError:
            # Si no es JSON válido, analizar texto plano
            safety_result = self._parse_text_response(content)
        
        # Añadir metadata
        safety_result["review_id"] = result.get("id", "unknown")
        safety_result["timestamp"] = datetime.now().isoformat()
        safety_result["model_used"] = self.model
        
        return safety_result
    
    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """Parsea respuesta de texto plano a JSON estructurado"""
        text_lower = text.lower()
        
        # Detección básica de problemas
        issues = []
        if "inapropiado" in text_lower or "no apropiado" in text_lower:
            issues.append("contenido_inapropiado")
        
        if "sesgo" in text_lower or "biased" in text_lower:
            issues.append("sesgo_detectado")
        
        if "privacidad" in text_lower or "personal" in text_lower:
            issues.append("informacion_personal")
        
        safe = len(issues) == 0 or "no" not in text_lower
        
        return {
            "safe": safe,
            "issues": issues,
            "severity": "medium" if issues else "low",
            "recommendations": [],
            "reason": text[:200]
        }


# Instancia global
_guard_agent: Optional[GuardAgent] = None


def get_guard_agent() -> GuardAgent:
    """Obtiene la instancia singleton del GuardAgent"""
    global _guard_agent
    if _guard_agent is None:
        _guard_agent = GuardAgent()
    return _guard_agent


def review_response(response_text: str, context: Optional[str] = None) -> Dict[str, Any]:
    """Función helper para revisar una respuesta"""
    agent = get_guard_agent()
    return agent.review_response(response_text, context)
