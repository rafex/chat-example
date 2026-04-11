# 🌤️ Chat CLI Interactivo - Agente Meteorológico

Un chat CLI interactivo con terminal colorful que consulta el clima de cualquier ciudad usando **OpenWeatherMap** y genera recomendaciones inteligentes con **DeepSeek**.

## 🚀 Cómo Usar

### Opción 1: Usando Just (Recomendado)

Desde el directorio raíz del proyecto:

```bash
# Iniciar chat interactivo
just chat

# Ver comandos disponibles
just chat-help

# Ejecutar pruebas
just chat-test
```

### Opción 2: Directamente con Python

```bash
cd poc/agent-weather
source venv/bin/activate
python src/chat_cli.py
```

## 📋 Comandos Disponibles en el Chat

| Comando | Descripción |
|---------|-------------|
| `salir` / `exit` / `quit` | Salir del chat |
| `limpiar` / `clear` / `cls` | Limpiar pantalla |
| `historial` / `history` | Ver historial reciente |
| `ayuda` | Ver ayuda del asistente |

## 💬 Ejemplos de Consultas

```
👤 Tu mensaje: ¿Cómo está el clima en Madrid?
🤖 CLIMA-BOT: 🌡️ **Clima en Madrid**
           • Temperatura: 25.0°C
           • Condición: cielo despejado
           • Humedad: 45%
           • Viento: 3.2 m/s

👤 Tu mensaje: ¿Qué tiempo hace en Barcelona?
🤖 CLIMA-BOT: [Información del clima de Barcelona...]

👤 Tu mensaje: ayuda
🤖 CLIMA-BOT: [Mostrar opciones de ayuda]
```

## 📁 Estructura del Proyecto

```
poc/agent-weather/
├── src/
│   ├── chat_cli.py              # Chat CLI interactivo principal
│   ├── schemas/
│   │   └── chat.py              # Modelos de sesión y mensajes
│   └── services/
│       └── weather_chat_agent.py # Agente de chat especializado
├── venv/                        # Entorno virtual
└── .env                         # API keys (no compartir)
```

## ⚙️ Funcionalidades

- **Terminal colorful**: Iconos y formato visual atractivo
- **Historial de sesión**: Mantiene registro de conversaciones
- **Reconocimiento de intenciones**: Detecta preguntas sobre clima
- **Extracción de ubicación**: Identifica ciudad en la consulta
- **Fallback automático**: Si la API falla, usa recomendaciones básicas
- **Comandos especiales**: Ayuda, historial, limpieza de pantalla

## 🔧 Configuración Requerida

Las API keys deben estar configuradas en `poc/agent-weather/.env`:

```bash
OPENWEATHER_API_KEY=tu_api_key_de_openweathermap
DEEPSEEK_API_KEY=tu_api_key_de_deepseek
```

## 🐛 Solución de Problemas

### "API key no válida"
- Espera 2 horas por la activación de OpenWeatherMap
- Verifica que las keys en `.env` sean correctas

### "No se pudo inicializar OpenAI"
- Es un warning técnico, el chat funciona igual
- DeepSeek usa un fallback automático

### "Error al consultar el clima"
- Verifica que la ciudad exista
- La API de OpenWeatherMap necesita estar activa (2h)

## 📚 Tecnologías

- **Python 3.9+**
- **LangGraph**: Orquestación de flujos
- **OpenWeatherMap API**: Datos climáticos reales
- **DeepSeek API**: Recomendaciones inteligentes
- **Pydantic**: Validación de datos
- **Colorama**: Colores en terminal

## 🎯 Próximos Pasos

1. **Espera 2 horas** a que se active OpenWeatherMap
2. **Ejecuta `just chat`** y prueba con diferentes ciudades
3. **Explora el código** en `src/chat_cli.py`
4. **Personaliza** las respuestas en `weather_chat_agent.py`

## 📝 Ejemplo de Ejecución

```bash
$ just chat

🌤️ Iniciando chat climatológico...

╔══════════════════════════════════════════════════════════════════════╗
║              🌤️  CHAT CLIMATOLÓGICO CON DEEPSEEK  🤖                 ║
╚══════════════════════════════════════════════════════════════════════╝

💡 Sesión iniciada: a1b2c3d4
💡 Escribe 'salir' o 'exit' para terminar

🤖 CLIMA-BOT: 👋 ¡Hola! Soy tu asistente meteorológico...

👤 Tu mensaje: ¿Cómo está el clima en Madrid?
🤖 CLIMA-BOT: 🌡️ **Clima en Madrid**
           • Temperatura: 25.0°C
           ...
```
