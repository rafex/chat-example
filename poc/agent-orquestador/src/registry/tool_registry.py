"""
Registro central de herramientas del sistema
"""
from typing import Dict, List, Optional, Any
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

# Intentar importar con diferentes enfoques
try:
    from src.schemas.tool import ToolDefinition, ToolInputSchema, ToolOutputSchema, ValidationResult
except ImportError:
    try:
        from schemas.tool import ToolDefinition, ToolInputSchema, ToolOutputSchema, ValidationResult
    except ImportError:
        try:
            # Import relativo desde registry
            from ..schemas.tool import ToolDefinition, ToolInputSchema, ToolOutputSchema, ValidationResult
        except ImportError:
            # Último recurso: import dinámico
            import importlib.util
            tool_path = os.path.join(current_dir, '..', 'schemas', 'tool.py')
            if os.path.exists(tool_path):
                spec = importlib.util.spec_from_file_location("tool_schema", tool_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    ToolDefinition = module.ToolDefinition
                    ToolInputSchema = module.ToolInputSchema
                    ToolOutputSchema = module.ToolOutputSchema
                    ValidationResult = module.ValidationResult
                else:
                    raise ImportError(f"No se pudo cargar tool.py desde {tool_path}")
            else:
                raise ImportError(f"Archivo no encontrado: {tool_path}")


class ToolRegistry:
    """
    Registro central de herramientas del sistema.
    Es la fuente única de verdad para qué herramientas existen y cómo se validan.
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._executors: Dict[str, callable] = {}
    
    def register(
        self,
        name: str,
        description: str,
        kind: str,
        executor: callable,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        available: bool = True,
        timeout: int = 10
    ) -> None:
        """
        Registra una herramienta en el sistema
        
        Args:
            name: Nombre único de la herramienta
            description: Descripción de la herramienta
            kind: Tipo de herramienta (agent, mcp, chat)
            executor: Función que ejecuta la herramienta
            input_schema: Schema de entrada (opcional)
            output_schema: Schema de salida (opcional)
            available: Si la herramienta está disponible
            timeout: Timeout en segundos
        """
        tool_schema = ToolInputSchema(**input_schema) if input_schema else ToolInputSchema()
        output_schema_obj = ToolOutputSchema(**output_schema) if output_schema else ToolOutputSchema()
        
        # Asegurar que kind sea un valor válido
        valid_kinds = {"agent", "mcp", "chat"}
        if kind not in valid_kinds:
            kind = "agent"  # Default fallback
        
        tool_def = ToolDefinition(
            name=name,
            description=description,
            kind=kind,  # type: ignore
            input_schema=tool_schema,
            output_schema=output_schema_obj,
            available=available,
            timeout=timeout
        )
        
        self._tools[name] = tool_def
        self._executors[name] = executor
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Obtiene la definición de una herramienta por nombre"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[ToolDefinition]:
        """Lista todas las herramientas registradas"""
        return list(self._tools.values())
    
    def list_available_tools(self) -> List[ToolDefinition]:
        """Lista solo las herramientas disponibles"""
        return [tool for tool in self._tools.values() if tool.available]
    
    def tool_exists(self, name: str) -> bool:
        """Verifica si una herramienta existe"""
        return name in self._tools
    
    def tool_available(self, name: str) -> bool:
        """Verifica si una herramienta existe y está disponible"""
        tool = self.get_tool(name)
        return tool is not None and tool.available
    
    def validate_call(self, tool_name: str, arguments: Dict[str, Any]) -> ValidationResult:
        """
        Valida una llamada a una herramienta
        
        Args:
            tool_name: Nombre de la herramienta
            arguments: Argumentos proporcionados
        
        Returns:
            ValidationResult con el resultado de la validación
        """
        # Verificar si la herramienta existe
        if not self.tool_exists(tool_name):
            return ValidationResult(
                valid=False,
                tool_name=tool_name,
                arguments=arguments,
                errors=[f"Herramienta no encontrada: {tool_name}"]
            )
        
        # Verificar si la herramienta está disponible
        if not self.tool_available(tool_name):
            return ValidationResult(
                valid=False,
                tool_name=tool_name,
                arguments=arguments,
                errors=[f"Herramienta no disponible: {tool_name}"]
            )
        
        tool = self.get_tool(tool_name)
        if tool is None:
            return ValidationResult(
                valid=False,
                tool_name=tool_name,
                arguments=arguments,
                errors=[f"Herramienta no encontrada (null check): {tool_name}"]
            )
        
        # Validar argumentos requeridos
        required_args = tool.input_schema.required
        missing_args = [arg for arg in required_args if arg not in arguments]
        
        if missing_args:
            return ValidationResult(
                valid=False,
                tool_name=tool_name,
                arguments=arguments,
                missing_arguments=missing_args,
                errors=[f"Faltan argumentos requeridos: {', '.join(missing_args)}"]
            )
        
        # Validar tipos de argumentos (simplificado - se podría extender con jsonschema)
        for arg_name, arg_value in arguments.items():
            if arg_name in tool.input_schema.properties:
                # Aquí se podría hacer validación de tipos más estricta
                prop = tool.input_schema.properties[arg_name]
                if 'type' in prop:
                    expected_type = prop['type']
                    if expected_type == 'string' and not isinstance(arg_value, str):
                        return ValidationResult(
                            valid=False,
                            tool_name=tool_name,
                            arguments=arguments,
                            errors=[f"Argumento '{arg_name}' debe ser string, got {type(arg_value).__name__}"]
                        )
        
        return ValidationResult(
            valid=True,
            tool_name=tool_name,
            arguments=arguments,
            errors=[],
            missing_arguments=[]
        )
    
    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """
        Ejecuta una herramienta validada
        
        Args:
            tool_name: Nombre de la herramienta
            arguments: Argumentos para la herramienta
        
        Returns:
            Resultado de la ejecución
        """
        if tool_name not in self._executors:
            raise ValueError(f"Herramienta no encontrada: {tool_name}")
        
        executor = self._executors[tool_name]
        return executor(**arguments)
    
    def get_tools_prompt_description(self) -> str:
        """
        Genera una descripción de las herramientas para incluir en el prompt del LLM
        """
        tools = self.list_available_tools()
        if not tools:
            return "No hay herramientas disponibles."
        
        descriptions = []
        for tool in tools:
            params_str = ""
            if tool.input_schema.required:
                params_str = f"({', '.join(tool.input_schema.required)})"
            
            descriptions.append(f"- {tool.name}{params_str}: {tool.description}")
        
        return "\n".join(descriptions)


# Instancia global del registro
tool_registry = ToolRegistry()
