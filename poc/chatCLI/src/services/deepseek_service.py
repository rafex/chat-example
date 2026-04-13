import os
import sys
from typing import List, Dict, Optional

# Importar configuración
current_dir = os.path.dirname(os.path.abspath(__file__))
try:
    from config import Config
except ImportError:
    # Fallback alternativo
    sys.path.insert(0, current_dir)
    from config import Config


class LLMProviderService:
    """Servicio para interactuar con proveedores LLM genéricos (compatible con OpenAI)"""

    def __init__(self):
        # Obtener configuración del proveedor actual
        config = Config.get_current_config()

        api_key = config.get("api_key")
        api_base = config.get("base_url")
        model = config.get("model")

        if not api_key:
            raise ValueError(f"API key no está configurada para el proveedor {Config.CURRENT_LLM_PROVIDER}")

        try:
            from openai import OpenAI
            import httpx

            # Establecer API key en variable de entorno para evitar problemas con httpx
            original_api_key = os.environ.get('OPENAI_API_KEY')
            os.environ['OPENAI_API_KEY'] = api_key

            # Limpiar variables de proxy que puedan causar problemas
            original_proxies = {}
            proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'all_proxy', 'ALL_PROXY']
            for var in proxy_vars:
                if var in os.environ:
                    original_proxies[var] = os.environ[var]
                    del os.environ[var]

            try:
                # Crear cliente httpx sin proxy
                http_client = httpx.Client(proxy=None)

                self.client = OpenAI(
                    api_key=api_key,
                    base_url=api_base,
                    http_client=http_client
                )
                self.model = model
                self.available = True
                print(f"✅ LLM Provider configurado: {api_base} (model: {model})")
            except Exception as e:
                print(f"⚠️ Error inicializando OpenAI client: {e}")
                raise
            finally:
                # Restaurar variables originales
                if original_api_key is not None:
                    os.environ['OPENAI_API_KEY'] = original_api_key
                elif 'OPENAI_API_KEY' in os.environ:
                    del os.environ['OPENAI_API_KEY']

                for var, value in original_proxies.items():
                    os.environ[var] = value

        except Exception as e:
            print(f"⚠️ No se pudo inicializar LLM Provider: {e}")
            import traceback
            traceback.print_exc()
            self.available = False

    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        """
        Realiza una conversación con el LLM usando formato OpenAI.

        Args:
            messages: Lista de mensajes en formato OpenAI
            model: Modelo a usar (por defecto el configurado)

        Returns:
            str: Respuesta del modelo
        """
        if not self.available:
            return "El servicio LLM no está disponible."

        if model is None:
            model = self.model

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )

            return response.choices[0].message.content.strip() if response.choices and response.choices[0].message.content else ""

        except Exception as e:
            print(f"Error en chat con LLM: {e}")
            return ""


# Backward compatibility: alias
DeepSeekService = LLMProviderService
