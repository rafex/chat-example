"""
Servicio de configuración basado en TOML.

Gestiona la configuración desde poc/config.toml y variables de entorno.
"""
import os
import toml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigService:
    """Servicio de configuración basado en TOML"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: Ruta al archivo config.toml (opcional)
        """
        # Determinar ruta del config.toml
        if config_path is None:
            # Buscar en el directorio actual y padres
            current_dir = Path(__file__).parent.parent.parent.parent
            self.config_path = current_dir / "config.toml"
            
            # Si no existe, usar el path relativo al proyecto
            if not self.config_path.exists():
                self.config_path = Path("poc/config.toml")
        else:
            self.config_path = Path(config_path)
        
        # Cargar configuración
        self._config = self._load_config()
        
        # Cargar variables de entorno
        self._env_vars = self._load_env_vars()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carga la configuración desde el archivo TOML"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return toml.load(f)
    
    def _load_env_vars(self) -> Dict[str, str]:
        """Carga variables de entorno relevantes"""
        env_vars = {}
        
        # API Keys de providers
        for provider in ['OPENAI_API_KEY', 'DEEPSEEK_API_KEY', 'OPENROUTER_API_KEY']:
            value = os.getenv(provider)
            if value:
                env_vars[provider] = value
        
        # API Key de OpenWeatherMap
        openweather_key = os.getenv('OPENWEATHER_API_KEY')
        if openweather_key:
            env_vars['OPENWEATHER_API_KEY'] = openweather_key
        
        return env_vars
    
    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Obtiene la configuración de un provider específico"""
        providers = self._config.get('providers', {})
        return providers.get(provider_name, {})
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Obtiene la configuración de un agente específico"""
        agents = self._config.get('agents', {})
        return agents.get(agent_name, {})
    
    def get_current_config(self) -> Dict[str, Any]:
        """Obtiene la configuración actual (provider por defecto + modelo)"""
        settings = self._config.get('settings', {})
        default_provider = settings.get('default_provider', 'deepseek')
        default_model = settings.get('default_model', 'deepseek-chat')
        
        provider_config = self.get_provider_config(default_provider)
        
        return {
            'provider': default_provider,
            'model': default_model,
            'base_url': provider_config.get('base_url', ''),
            'api_key': self._env_vars.get(f'{default_provider.upper()}_API_KEY', '')
        }
    
    def get_model_config(self, provider_name: str, model_name: str) -> Dict[str, Any]:
        """Obtiene configuración específica para un modelo"""
        provider_config = self.get_provider_config(provider_name)
        
        return {
            'provider': provider_name,
            'model': model_name,
            'base_url': provider_config.get('base_url', ''),
            'api_key': self._env_vars.get(f'{provider_name.upper()}_API_KEY', '')
        }
    
    def set_provider(self, provider_name: str):
        """Cambia el provider por defecto"""
        if provider_name not in self._config.get('providers', {}):
            raise ValueError(f"Provider '{provider_name}' no configurado")
        
        self._config['settings']['default_provider'] = provider_name
        
        # Guardar cambios
        with open(self.config_path, 'w', encoding='utf-8') as f:
            toml.dump(self._config, f)
    
    def set_model(self, model_name: str):
        """Cambia el modelo por defecto"""
        self._config['settings']['default_model'] = model_name
        
        # Guardar cambios
        with open(self.config_path, 'w', encoding='utf-8') as f:
            toml.dump(self._config, f)
    
    def is_guard_enabled(self) -> bool:
        """Verifica si el agente de seguridad está habilitado"""
        guard_config = self.get_agent_config('guard')
        return guard_config.get('enabled', False)
    
    def get_guard_config(self) -> Dict[str, Any]:
        """Obtiene la configuración del agente de seguridad"""
        return self.get_agent_config('guard')


# Instancia global del servicio de configuración
_config_service: Optional[ConfigService] = None


def get_config_service() -> ConfigService:
    """
    Obtiene la instancia singleton del servicio de configuración
    
    Returns:
        Instancia del ConfigService
    """
    global _config_service
    if _config_service is None:
        _config_service = ConfigService()
    return _config_service


def reset_config_service():
    """Resetea la instancia de configuración (útil para tests)"""
    global _config_service
    _config_service = None
