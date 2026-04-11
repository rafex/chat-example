# 🌤️ Chat CLI - Guía de Uso Rápida

## Inicio Rápido

```bash
# Desde el directorio raíz
just chat

# O directamente
cd poc/agent-weather
source venv/bin/activate
python src/chat_cli.py
```

## Comandos en el Chat

| Comando | Descripción |
|---------|-------------|
| `salir`, `exit`, `quit` | Salir del chat |
| `limpiar`, `clear` | Limpiar pantalla |
| `historial` | Ver últimas 5 interacciones |
| `ayuda` | Mostrar ayuda |

## Ejemplos de Uso

```
👤 Tu mensaje: ¿Cómo está el clima en Madrid?
🤖 CLIMA-BOT: 🌡️ **Clima en Madrid**
           • Temperatura: 25.0°C
           • Condición: cielo despejado
           • Humedad: 45%
           • Viento: 3.2 m/s

👤 Tu mensaje: ¿Qué tiempo hace en Barcelona?
🤖 CLIMA-BOT: [Información del clima...]

👤 Tu mensaje: ayuda
🤖 CLIMA-BOT: [Mostrar opciones de ayuda]

👤 Tu mensaje: adiós
🤖 CLIMA-BOT: 👋 ¡Hasta pronto! Que tengas un buen día.
```

## APIs Configuradas

- **OpenWeatherMap**: Datos climáticos reales
- **DeepSeek**: Recomendaciones inteligentes

## Notas Importantes

1. La API de OpenWeatherMap necesita 2h para activarse
2. Si la API no está activa, se usa un fallback con datos simulados
3. DeepSeek puede mostrar warning de `proxies`, pero funciona igual

## Resumen de Comandos Just

```bash
just chat              # Iniciar chat interactivo
just chat-test         # Ejecutar pruebas del chat
just chat-help         # Ver comandos disponibles
just install-chat      # Instalar dependencias del chat
```
