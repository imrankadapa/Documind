---
description: Keep this FastAPI and Streamlit student project simple and easy to explain.
applyTo: '**/*'
---

# Project style

- Prefer small functions and direct code over extra classes, factories, or service layers.
- Keep the current flow easy to follow: Streamlit -> FastAPI -> document extraction -> FAISS -> optional Neo4j -> Ollama.
- Add new endpoints or fields without breaking the existing upload and `/llm` API.
- Neo4j is an optional helper for graph facts. FAISS remains the main document search.
- Use clear error messages and simple defaults. Avoid adding libraries unless the feature really needs them.
- When changing the UI, keep the dark theme and use Streamlit components rather than introducing another frontend framework.
