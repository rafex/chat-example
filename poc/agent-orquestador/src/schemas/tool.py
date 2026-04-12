"""
Schemas para el registro de herramientas
"""
from typing import Dict, List, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ToolInputSchema(BaseModel):
    """Schema de entrada para una herramienta"""
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class ToolOutputSchema(BaseModel):
    """Schema de salida para una herramienta"""
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)


class ToolDefinition(BaseModel):
    """Definición completa de una herramienta"""
    name: str = Field(..., description="Nombre único de la herramienta")
    description: str = Field(..., description="Descripción de la herramienta")
    kind: Literal["agent", "mcp", "chat"] = Field(..., description="Tipo de herramienta")
    input_schema: ToolInputSchema = Field(default_factory=ToolInputSchema)
    output_schema: ToolOutputSchema = Field(default_factory=ToolOutputSchema)
    available: bool = Field(default=True, description="Si la herramienta está disponible")
    timeout: int = Field(default=10, description="Timeout en segundos")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ValidationResult(BaseModel):
    """Resultado de la validación de una llamada a herramienta"""
    valid: bool = Field(..., description="Si la validación fue exitosa")
    tool_name: str = Field(..., description="Nombre de la herramienta validada")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Argumentos validados")
    errors: List[str] = Field(default_factory=list, description="Lista de errores si hay")
    missing_arguments: List[str] = Field(default_factory=list, description="Argumentos faltantes")
    corrected: bool = Field(default=False, description="Si los argumentos fueron corregidos")
