# Manager Agent

Agente personal para RETO_IA 1 que responde preguntas sobre la carrera, habilidades y experiencia de **David de la Cruz**.

## Descripción

Este agente combina:
- **RAG** (Retrieval-Augmented Generation) con Supabase y Mistral embeddings.
- **Pydantic AI** para la generación de respuestas conversacionales.
- **FastAPI** como servidor web.
- **OpenAI** como modelo de lenguaje.

El agente expone un endpoint compatible con **OpenAI Responses API** y una tarjeta de agente (`.well-known/agent-card.json`) para ser integrado en plataformas de terceros.

## Arquitectura
