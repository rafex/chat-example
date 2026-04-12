"""
Schemas para el Agente Orquestador
"""

from typing import TypedDict, Optional, Sequence, Literal, Any, List
from datetime import datetime


# Tipos de herramientas disponibles
ToolType = Literal["weather", "mcp", "chat", "memory"]


class OrquestadorState(TypedDict):
    """
    Estado ampliado del agente orquestador
    
    Campos:
        session_id: Identificador de la sesión
        turn_id: Número de turno en la sesión
        user_message: Mensaje del usuario
        conversation_history: Historial de la conversación
        retrieved_memories: Memoria semántica recuperada de FAISS
        available_tools: Lista de nombres de herramientas disponibles
        llm_decision: Decisión cruda del LLM (JSON parseado)
        validation_result: Resultado de la validación
        tool_result: Resultado de la ejecución de herramienta
        final_response: Respuesta final al usuario
        errors: Lista de errores durante el procesamiento
    """
    session_id: str
    turn_id: int
    user_message: str
    conversation_history: List[dict[str, str]]
    retrieved_memories: List[dict[str, Any]]
    available_tools: List[str]
    llm_decision: Optional[dict[str, Any]]
    validation_result: Optional[dict[str, Any]]
    tool_result: Optional[dict[str, Any]]
    final_response: Optional[str]
    errors: List[str]
    
    # Campos heredados para compatibilidad
    user_input: str  # Alias para user_message
    intent: Optional[str]
    tool_to_use: Optional[ToolType]
    tool_args: Optional[dict[str, Any]]
    response: Optional[str]
    history: Sequence[dict[str, str]]
    error: Optional[str]


class IntentAnalysis(TypedDict):
    """Resultado del análisis de intención"""
    intent: str
    confidence: float
    tool_type: ToolType
    arguments: dict[str, Any]


class ToolExecutionResult(TypedDict):
    """Resultado de la ejecución de una herramienta"""
    success: bool
    tool_used: ToolType
    tool_args: dict[str, Any]
    response: str
    timestamp: datetime


# Constantes para eventos de observabilidad
EVENT_LLM_DECISION = "llm_decision"
EVENT_TOOL_VALIDATION = "tool_validation"
EVENT_TOOL_EXECUTION = "tool_execution"
EVENT_MEMORY_PERSISTED = "memory_persisted"
EVENT_ERROR = "error"
