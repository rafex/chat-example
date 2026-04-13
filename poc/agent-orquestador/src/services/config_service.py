"""
Servicio de configuración del orquestador.
Gestiona variables de entorno y modos de operación.
"""
import os
from typing import Literal, Optional
from enum import Enum

# Modos de operación
OperationMode = Literal["strict", "flexible"]


class OrchestratorConfig:
    """Configuración del orquestador"""
    
    def __init__(self):
        self.mode: OperationMode = self._load_mode()
        self.debug: bool = self._load_debug()
    
    def _load_mode(self) -> OperationMode:
        """Carga el modo de operación desde variable de entorno"""
        mode_str = os.getenv("ORCHESTRATOR_MODE", "strict").lower()
        
        if mode_str not in ["strict", "flexible"]:
            print(f"⚠️  Modo '{mode_str}' no reconocido. Usando 'strict' por defecto.")
            return "strict"
        
        return mode_str
    
    def _load_debug(self) -> bool:
        """Carga el flag de debug desde variable de entorno"""
        debug_str = os.getenv("ORCHESTRATOR_DEBUG", "false").lower()
        return debug_str in ["true", "1", "yes", "on"]
    
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
