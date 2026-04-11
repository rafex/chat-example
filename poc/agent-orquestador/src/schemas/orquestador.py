"""
Schemas para el Agente Orquestador
"""

from typing import TypedDict, Optional, Sequence, Literal, Any
from datetime import datetime


# Tipos de herramientas disponibles
ToolType = Literal["weather", "mcp", "chat", "memory"]


class OrquestadorState(TypedDict):
    """Estado del agente orquestador"""
    user_input: str
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
