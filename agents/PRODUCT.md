# PRODUCT

## Problem
Construir un sistema de chat inteligente basado en LangGraph que demuestre cómo un agente orquestador puede decidir, validar y usar distintas herramientas disponibles para resolver solicitudes del usuario sin inventar capacidades inexistentes.

## Users
- Desarrolladores de IA que necesitan demostrar arquitecturas de orquestación
- Usuarios finales que interactúan con un chatbot multi-herramienta
- Equipos técnicos que evalúan integridad de sistemas de herramientas

## Goals
- Proveer una interfaz de entrada y salida de texto para conversación
- Incorporar memoria semántica usando FAISS para recuperar contexto relevante
- Usar un agente orquestador que decida cuándo responder directamente y cuándo usar una herramienta
- Integrar herramientas reales disponibles (clima, MCP, fallback conversacional)
- Evitar que el sistema invente herramientas, MCPs o capacidades inexistentes

## Exclusions
- No es un chatbot enfocado en una sola tarea
- No inventa herramientas o APIs no integradas
- No asume acceso a web, cálculo, archivos o APIs no integradas

## Value Proposition
El orquestador no debe responder "como si supiera hacer algo", sino decidir si existe una herramienta real disponible para resolver la necesidad del usuario, validarla y ejecutarla de forma controlada.
