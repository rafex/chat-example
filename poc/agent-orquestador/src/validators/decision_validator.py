"""
Validador de decisiones del LLM
"""
import json
from typing import Dict, Any, Optional, Tuple
import os
import sys

# Añadir el directorio padre al path para imports relativos
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.dirname(parent_dir)

# Añadir src al path si no está
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Intentar importar
try:
    from src.registry.tool_registry import tool_registry
    from src.schemas.tool import ValidationResult
except ImportError:
    try:
        from registry.tool_registry import tool_registry
        from schemas.tool import ValidationResult
    except ImportError:
        try:
            # Import relativo
            from ..registry.tool_registry import tool_registry
            from ..schemas.tool import ValidationResult
        except ImportError:
            raise ImportError("No se pudo importar tool_registry o ValidationResult")


class DecisionValidator:
    """
    Valida determinísticamente las decisiones producidas por el LLM
    """
    
    @staticmethod
    def parse_llm_response(response_text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Parsea la respuesta JSON del LLM
        
        Returns:
            Tupla con (parsed_dict, error_message)
        """
        try:
            # Intentar extraer JSON del texto
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start == -1 or end == 0:
                return None, "No se encontró JSON en la respuesta"
            
            json_text = response_text[start:end]
            parsed = json.loads(json_text)
            
            if not isinstance(parsed, dict):
                return None, "El JSON no es un objeto"
            
            return parsed, None
            
        except json.JSONDecodeError as e:
            return None, f"JSON inválido: {str(e)}"
        except Exception as e:
            return None, f"Error parseando respuesta: {str(e)}"
    
    @staticmethod
    def validate_decision(llm_decision: Dict[str, Any]) -> ValidationResult:
        """
        Valida una decisión del LLM
        
        Args:
            llm_decision: Diccionario con la decisión del LLM
        
        Returns:
            ValidationResult con el resultado de la validación
        """
        # Extraer información de la decisión
        tool_name = llm_decision.get('tool_name')
        arguments = llm_decision.get('arguments', {})
        requires_tool = llm_decision.get('requires_tool', False)
        intent = llm_decision.get('intent', '')
        
        # Si no requiere herramienta, es una decisión válida para chat genérico
        if not requires_tool:
            return ValidationResult(
                valid=True,
                tool_name=tool_name or 'chat',
                arguments=arguments,
                errors=[],
                missing_arguments=[]
            )
        
        # Si requiere herramienta pero no se especifica cuál
        if not tool_name:
            return ValidationResult(
                valid=False,
                tool_name='unknown',
                arguments=arguments,
                errors=['El LLM indicó que requiere herramienta pero no especificó cuál'],
                missing_arguments=[]
            )
        
        # Validar contra el registro de herramientas
        return tool_registry.validate_call(tool_name, arguments)
    
    @staticmethod
    def sanitize_llm_decision(raw_decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Limpia y normaliza la decisión del LLM para garantizar coherencia
        
        Args:
            raw_decision: Decisión cruda del LLM
        
        Returns:
            Decisión normalizada
        """
        normalized = {
            'intent': raw_decision.get('intent', 'unknown'),
            'tool_type': raw_decision.get('tool_type', 'chat'),
            'tool_name': raw_decision.get('tool_name'),
            'arguments': raw_decision.get('arguments', {}),
            'confidence': raw_decision.get('confidence', 0.5),
            'requires_tool': raw_decision.get('requires_tool', False),
            'reasoning_summary': raw_decision.get('reasoning_summary', ''),
            'missing_arguments': raw_decision.get('missing_arguments', [])
        }
        
        # Si no hay tool_name pero requires_tool es True, marcar como error
        if normalized['requires_tool'] and not normalized['tool_name']:
            normalized['requires_tool'] = False
        
        return normalized
