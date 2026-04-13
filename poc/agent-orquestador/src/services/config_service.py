"""
Servicio de configuración del orquestador.
Wrapper para compatibilidad con config_toml_service.
"""
import os
from typing import Literal, Optional

# Modos de operación
OperationMode = Literal["strict", "flexible"]


class OrchestratorConfig:
    """Configuración del orquestador (wrapper para config_toml_service)"""
    
    def __init__(self):
        # Importar dinámicamente para evitar dependencias circulares
        try:
            from services.config_toml_service import get_config_service
            self.toml_config = get_config_service()
        except ImportError:
            self.toml_config = None
        
        self.mode: OperationMode = self._load_mode()
        self.debug: bool = self._load_debug()
    
    def _load_mode(self) -> OperationMode:
        """Carga el modo de operación desde variable de entorno o config TOML"""
        # Primero intentar variable de entorno
        mode_str = os.getenv("ORCHESTRATOR_MODE", "").lower()
        
        if not mode_str and self.toml_config:
            # Si no hay variable de entorno, intentar config TOML
            agent_config = self.toml_config.get_agent_config("orquestador")
            mode_str = agent_config.get("mode", "strict").lower()
        
        if not mode_str:
            mode_str = "strict"
        
        if mode_str not in ["strict", "flexible"]:
            print(f"⚠️  Modo '{mode_str}' no reconocido. Usando 'strict' por defecto.")
            return "strict"
        
        return mode_str
    
    def _load_debug(self) -> bool:
        """Carga el flag de debug desde variable de entorno o config TOML"""
        # Primero intentar variable de entorno
        debug_str = os.getenv("ORCHESTRATOR_DEBUG", "").lower()
        
        if not debug_str and self.toml_config:
            # Si no hay variable de entorno, intentar config TOML
            settings = self.toml_config._config.get("settings", {})
            debug_str = str(settings.get("debug_mode", False)).lower()
        
        if not debug_str:
            debug_str = "false"
        
        return debug_str in ["true", "1", "yes", "on", "true"]
    
    def is_strict_mode(self) -> bool:
        """Verifica si está en modo estricto"""
        return self.mode == "strict"
    
    def is_flexible_mode(self) -> bool:
        """Verifica si está en modo flexible"""
        return self.mode == "flexible"
    
    def get_mode_description(self) -> str:
        """Obtiene la descripción del modo actual"""
        if self.is_strict_mode():
            return (
                "Modo STRICT: Solo usa herramientas reales, no inventa capacidades, "
                "respuesta controlada cuando no existe herramienta. Ideal para validar."
            )
        else:
            return (
                "Modo FLEXIBLE: Permite respuesta conversacional adicional, útil para pruebas. "
                "Aun así no inventa herramientas inexistentes."
            )
    
    def get_provider_config(self, provider_name: str) -> dict:
        """Obtiene configuración de provider desde TOML"""
        if self.toml_config:
            return self.toml_config.get_provider_config(provider_name)
        return {}
    
    def get_current_config(self) -> dict:
        """Obtiene configuración actual desde TOML"""
        if self.toml_config:
            return self.toml_config.get_current_config()
        return {}


# Instancia global de configuración
_config: Optional[OrchestratorConfig] = None


def get_config() -> OrchestratorConfig:
    """Obtiene la instancia singleton de configuración"""
    global _config
    if _config is None:
        _config = OrchestratorConfig()
    return _config


def reset_config():
    """Resetea la configuración (útil para tests)"""
    global _config
    _config = None
