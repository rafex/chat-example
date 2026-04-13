"""
Servicio de gestión de prompts desde TOML.

Carga y gestiona los prompts de sistema desde poc/prompts.toml.
"""
import toml
from pathlib import Path
from typing import Dict, Any, Optional


class PromptService:
    """Servicio para cargar prompts desde TOML"""
    
    def __init__(self, prompts_path: Optional[str] = None):
        """
        Args:
            prompts_path: Ruta al archivo prompts.toml (opcional)
        """
        # Determinar ruta del prompts.toml
        if prompts_path is None:
            current_dir = Path(__file__).parent.parent.parent.parent
            self.prompts_path = current_dir / "poc" / "prompts.toml"
            
            # Si no existe, buscar en el directorio padre
            if not self.prompts_path.exists():
                self.prompts_path = current_dir / "prompts.toml"
        else:
            self.prompts_path = Path(prompts_path)
        
        # Cargar prompts
        self._prompts = self._load_prompts()
    
    def _load_prompts(self) -> Dict[str, Any]:
        """Carga los prompts desde el archivo TOML"""
        if not self.prompts_path.exists():
            raise FileNotFoundError(f"Prompts file not found: {self.prompts_path}")
        
        with open(self.prompts_path, 'r', encoding='utf-8') as f:
            return toml.load(f)
    
    def get_prompt(self, agent_name: str, prompt_type: str = "system_prompt") -> str:
        """
        Obtiene un prompt específico para un agente
        
        Args:
            agent_name: Nombre del agente (orquestador, guard, chat, weather)
            prompt_type: Tipo de prompt a obtener
            
        Returns:
            Texto del prompt
        """
        agent_config = self._prompts.get("agents", {}).get(agent_name, {})
        
        if prompt_type == "system_prompt":
            return agent_config.get("system_prompt", "")
        
        return ""
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Obtiene la configuración completa de un agente
        
        Args:
            agent_name: Nombre del agente
            
        Returns:
            Configuración del agente
        """
        return self._prompts.get("agents", {}).get(agent_name, {})
    
    def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """
        Obtiene configuración de un modelo
        
        Args:
            model_name: Nombre del modelo
            
        Returns:
            Configuración del modelo
        """
        models = self._prompts.get("models", {})
        return models.get(model_name, {})
    
    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """
        Obtiene configuración de un provider
        
        Args:
            provider_name: Nombre del provider
            
        Returns:
            Configuración del provider
        """
        providers = self._prompts.get("providers", {})
        return providers.get(provider_name, {})


# Instancia global del servicio de prompts
_prompt_service: Optional[PromptService] = None


def get_prompt_service() -> PromptService:
    """
    Obtiene la instancia singleton del servicio de prompts
    
    Returns:
        Instancia del PromptService
    """
    global _prompt_service
    if _prompt_service is None:
        _prompt_service = PromptService()
    return _prompt_service


def reset_prompt_service():
    """Resetea la instancia de prompts (útil para tests)"""
    global _prompt_service
    _prompt_service = None
