# DocuMind Vite frontend

This folder contains the Vite + React JSX frontend based on the supplied
Document Q&A design. It uses the real FastAPI endpoints:

- `GET /health`
- `POST /documents/upload`
- `GET /llm`

Run it with:

```powershell
cd "C:\Users\kadap\Pictures\FastApi\frontend 2"
npm install
Copy-Item .env.example .env
npm run dev
```

The chat starts empty. Documents and answers come from the running backend;
the example conversation from the visual reference is not hardcoded.
Visible citations show only the returned source filenames.
