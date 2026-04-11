import sys
import os
from dotenv import load_dotenv

# Agregar el directorio raíz del proyecto al Python path
# El directorio actual es src/tests, el raíz del proyecto es poc/agent-weather
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Cargar variables de entorno desde .env (en el root del proyecto poc/agent-weather)
env_path = os.path.join(project_root, '..', '.env')
load_dotenv(dotenv_path=env_path)
