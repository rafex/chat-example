"""
Módulo de logging estructurado para el orquestador
"""
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional


class OrquestadorLogger:
    """
    Logger estructurado para el agente orquestador
    """
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.session_logs = {}
    
    def log_event(
        self,
        session_id: str,
        turn_id: int,
        event_type: str,
        status: str = "success",
        tool_name: Optional[str] = None,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        latency_ms: Optional[float] = None
    ) -> None:
        """
        Registra un evento estructurado
        
        Args:
            session_id: Identificador de sesión
            turn_id: Número de turno
            event_type: Tipo de evento
            status: Estado del evento (success, error, warning)
            tool_name: Nombre de la herramienta (si aplica)
            message: Mensaje descriptivo
            details: Detalles adicionales en formato dict
            latency_ms: Latencia en milisegundos
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "turn_id": turn_id,
            "event_type": event_type,
            "status": status,
            "tool_name": tool_name,
            "message": message,
            "details": details or {},
            "latency_ms": latency_ms
        }
        
        # Guardar en sesión
        if session_id not in self.session_logs:
            self.session_logs[session_id] = []
        self.session_logs[session_id].append(log_entry)
        
        # Imprimir en modo debug
        if self.debug_mode:
            print(json.dumps(log_entry, indent=2, ensure_ascii=False))
        else:
            # Formato compacto para producción
            # Formatear timestamp manualmente para evitar dependencia circular
            try:
                dt = datetime.fromisoformat(log_entry['timestamp'])
                timestamp_str = dt.strftime("%H:%M:%S")
            except:
                timestamp_str = log_entry['timestamp'][:19]
            
            prefix = f"[{timestamp_str}] {event_type.upper()}"
            if tool_name:
                prefix += f" [{tool_name}]"
            
            status_symbol = "✅" if status == "success" else "⚠️" if status == "warning" else "❌"
            print(f"{status_symbol} {prefix}: {message or ''}")
            
            if details and self.debug_mode:
                print(f"   Detalles: {json.dumps(details, ensure_ascii=False)}")
    
    def log_llm_decision(
        self,
        session_id: str,
        turn_id: int,
        user_message: str,
        llm_decision: Dict[str, Any],
        latency_ms: float
    ) -> None:
        """
        Registra una decisión del LLM
        """
        self.log_event(
            session_id=session_id,
            turn_id=turn_id,
            event_type="llm_decision",
            status="success",
            message=f"Decisión del LLM: {llm_decision.get('intent')}",
            details={
                "user_message": user_message[:100],  # Truncar para evitar logs muy largos
                "tool_name": llm_decision.get('tool_name'),
                "tool_type": llm_decision.get('tool_type'),
                "confidence": llm_decision.get('confidence'),
                "arguments": llm_decision.get('arguments', {})
            },
            latency_ms=latency_ms
        )
    
    def log_tool_validation(
        self,
        session_id: str,
        turn_id: int,
        tool_name: str,
        valid: bool,
        errors: list,
        latency_ms: float
    ) -> None:
        """
        Registra la validación de una herramienta
        """
        self.log_event(
            session_id=session_id,
            turn_id=turn_id,
            event_type="tool_validation",
            status="success" if valid else "error",
            tool_name=tool_name,
            message=f"Herramienta {'validada' if valid else 'rechazada'}: {tool_name}",
            details={
                "valid": valid,
                "errors": errors
            },
            latency_ms=latency_ms
        )
    
    def log_tool_execution(
        self,
        session_id: str,
        turn_id: int,
        tool_name: str,
        success: bool,
        latency_ms: float
    ) -> None:
        """
        Registra la ejecución de una herramienta
        """
        self.log_event(
            session_id=session_id,
            turn_id=turn_id,
            event_type="tool_execution",
            status="success" if success else "error",
            tool_name=tool_name,
            message=f"Ejecución de herramienta {'exitosa' if success else 'fallida'}: {tool_name}",
            latency_ms=latency_ms
        )
    
    def log_memory_persisted(
        self,
        session_id: str,
        turn_id: int,
        memory_type: str
    ) -> None:
        """
        Registra la persistencia de memoria
        """
        self.log_event(
            session_id=session_id,
            turn_id=turn_id,
            event_type="memory_persisted",
            status="success",
            message=f"Memoria persistida: {memory_type}"
        )
    
    def log_error(
        self,
        session_id: str,
        turn_id: int,
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra un error
        """
        self.log_event(
            session_id=session_id,
            turn_id=turn_id,
            event_type="error",
            status="error",
            message=message,
            details={
                "error_type": error_type,
                **(details or {})
            }
        )
    
    def get_session_logs(self, session_id: str) -> list:
        """
        Obtiene todos los logs de una sesión
        """
        return self.session_logs.get(session_id, [])
    
    def clear_session_logs(self, session_id: str) -> None:
        """
        Limpia los logs de una sesión
        """
        if session_id in self.session_logs:
            del self.session_logs[session_id]


def timestamp_format(iso_timestamp: str) -> str:
    """
    Formatea un timestamp ISO a formato legible
    """
    dt = datetime.fromisoformat(iso_timestamp)
    return dt.strftime("%H:%M:%S")


# Instancia global del logger
logger = OrquestadorLogger(debug_mode=False)


def set_debug_mode(debug: bool) -> None:
    """
    Activa/desactiva el modo debug del logger
    """
    global logger
    logger.debug_mode = debug
