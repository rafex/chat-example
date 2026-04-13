"""
Servicio de sesión para manejar el ciclo de vida de la memoria.
La memoria es efímera y se elimina al cerrar la sesión.
"""
import os
import shutil
import atexit
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from .memory_service import get_memory_service, clear_memory_cache
from .config_service import get_config


class SessionManager:
    """Gestor de sesiones con memoria efímera"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.config = get_config()
        
        # Registrar limpieza automática al salir del programa
        atexit.register(self.cleanup_all_sessions)
    
    def create_session(self, session_id: str) -> Dict[str, Any]:
        """
        Crea una nueva sesión con su memoria asociada
        
        Args:
            session_id: Identificador único de la sesión
            
        Returns:
            Diccionario con información de la sesión
        """
        # Crear directorio temporal para la sesión
        temp_dir = Path.home() / ".agentes-langgraph" / "temp_sessions"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear memoria para la sesión
        memory_service = get_memory_service(session_id)
        
        session_info = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "memory_service": memory_service,
            "temp_dir": str(temp_dir / session_id),
            "is_active": True
        }
        
        self.active_sessions[session_id] = session_info
        
        # Registrar creación de sesión
        if self.config.debug:
            print(f"✅ Sesión creada: {session_id}")
        
        return session_info
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de una sesión activa
        
        Args:
            session_id: Identificador de la sesión
            
        Returns:
            Información de la sesión o None si no existe
        """
        return self.active_sessions.get(session_id)
    
    def close_session(self, session_id: str) -> bool:
        """
        Cierra una sesión y limpia su memoria
        
        Args:
            session_id: Identificador de la sesión
            
        Returns:
            True si la sesión fue cerrada, False si no existía
        """
        if session_id not in self.active_sessions:
            return False
        
        session_info = self.active_sessions[session_id]
        
        # Limpiar memoria de la sesión
        try:
            memory_service = session_info.get("memory_service")
            if memory_service:
                memory_service.clear_all()
                memory_service.save()  # Guardar estado limpio
                
            # Eliminar archivos temporales de la sesión
            temp_dir = session_info.get("temp_dir")
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            if self.config.debug:
                print(f"⚠️  Error limpiando sesión {session_id}: {e}")
        
        # Remover de sesiones activas
        del self.active_sessions[session_id]
        
        # Registrar cierre de sesión
        if self.config.debug:
            print(f"✅ Sesión cerrada: {session_id}")
        
        return True
    
    def cleanup_all_sessions(self):
        """Limpia todas las sesiones activas"""
        session_ids = list(self.active_sessions.keys())
        for session_id in session_ids:
            self.close_session(session_id)
        
        # Limpiar cache global de memoria
        clear_memory_cache()
        
        if self.config.debug:
            print("✅ Todas las sesiones han sido cerradas")


# Instancia global del gestor de sesiones
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Obtiene la instancia global del gestor de sesiones
    
    Returns:
        Instancia singleton del SessionManager
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def cleanup_sessions():
    """Limpia todas las sesiones activas"""
    manager = get_session_manager()
    manager.cleanup_all_sessions()
