# DocuMind

DocuMind is a simple local document question-answering project. The user
uploads PDF, TXT, or DOCX files, and then asks questions about their content.
FastAPI extracts and indexes the text, FAISS finds relevant passages, and
Ollama generates the answer locally.

This is a student-friendly prototype. The main working path is:

```text
Frontend -> FastAPI -> Document extraction -> Chunking
         -> Sentence Transformer -> FAISS -> Ollama -> Answer + sources
```

Neo4j is an optional extra for simple entity and relationship facts. It is not
required for the main FAISS search.

## Project structure

```text
FastApi/
├── backend/
│   ├── main.py                 # FastAPI endpoints and upload/chat flow
│   ├── embedding_model.py      # Loads all-MiniLM-L6-v2
│   ├── graph_service.py        # Optional Neo4j support
│   ├── requirements.txt        # Backend Python packages
│   ├── services/
│   │   └── document_service.py # Extract, chunk, index, and search functions
│   ├── uploads/                # Original uploaded files
│   ├── documents.json          # Uploaded document information
│   ├── texts.npy               # Saved chunk metadata
│   └── vector.index            # FAISS index
├── frontend/
│   ├── frontend.py             # Original Streamlit frontend
│   └── requirements.txt
├── frontend 2/
│   ├── src/main.jsx            # Vite/React chat frontend
│   ├── src/style.css           # Reference chat layout styling
│   └── package.json            # React frontend dependencies
├── Documinds1.docx             # Research paper
├── PROJECT_DOCUMENTATION.md    # Complete backend and Streamlit project report
├── README.md                   # This project guide
└── .github/instructions/       # Project coding style
```

Generated files such as `vector.index`, `texts.npy`, and `documents.json` are
created by the backend. Do not edit them manually.

## How the project works

### Upload

1. The frontend sends one or more files as `multipart/form-data`.
2. FastAPI checks the file extension.
3. The original file is saved with a random name in `backend/uploads/`.
4. `pdf_extract`, `txt_extract`, or `doc_extract` reads the file.
5. Text is cleaned and split into small chunks.
6. `all-MiniLM-L6-v2` creates an embedding for every chunk.
7. FAISS stores the embeddings and the chunk metadata is saved in `texts.npy`.
8. The API returns a document ID, filename, type, and chunk count.

Supported files:

| Extension | Extractor |
|---|---|
| `.pdf` | PyMuPDF |
| `.txt` | Python text reading with UTF-8 |
| `.docx` | python-docx paragraphs and tables |

### Question answering

1. The frontend sends `query` and optional `document_ids` to `/llm`.
2. The question is converted into an embedding.
3. FAISS returns the closest chunks.
4. The selected chunks are placed in the Ollama prompt.
5. Ollama answers using the retrieved document context.
6. The response includes the answer, sources, and optional graph facts.

Each source contains the filename, document ID, chunk number, passage, rank,
and FAISS distance. The UI uses the filename as the visible citation.
FAISS distance is only a retrieval signal; it is not a formal confidence
score.

## Running the project

Open separate PowerShell terminals.

### 1. Backend

```powershell
cd C:\Users\kadap\Pictures\FastApi\backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
API docs: http://127.0.0.1:8000/docs
Health:   http://127.0.0.1:8000/health
```

### 2. Ollama

Start this manually when you want answers:

```powershell
ollama serve
ollama run llama3.2
```

The backend returns a clear error if Ollama is not running. Uploading and
indexing documents do not require Ollama.

### 3. Streamlit frontend

```powershell
cd C:\Users\kadap\Pictures\FastApi\frontend
pip install -r requirements.txt
streamlit run frontend.py
```

Streamlit:

```text
http://localhost:8501
```

## Optional Neo4j setup

Neo4j is optional. FAISS remains the main document retriever.

Install Neo4j Desktop from:

```text
https://neo4j.com/download/
```

Create and start a local database named `RAG`. Configure the connection with:

```text
URI:      neo4j://127.0.0.1:7687
Username: neo4j
Password: set `NEO4J_PASSWORD` in your environment
Database: RAG
Browser:  http://localhost:7474
```

Set these variables in the same terminal before starting FastAPI:

```powershell
$env:NEO4J_URI="neo4j://127.0.0.1:7687"
$env:NEO4J_USERNAME="neo4j"
$env:NEO4J_PASSWORD="your-neo4j-password"
$env:NEO4J_DATABASE="RAG"
```

Check the connection:

```text
http://127.0.0.1:8000/health
```

Example response:

```json
{
  "backend": "ok",
  "neo4j": "connected"
}
```

The graph created during upload is:

```text
(Document)-[:HAS_CHUNK]->(Chunk)-[:MENTIONS]->(Entity)
```

Useful Neo4j Browser queries:

```cypher
MATCH (n)-[r]->(m)
RETURN n, r, m
LIMIT 100;
```

```cypher
MATCH (document:Document)-[:HAS_CHUNK]->(chunk:Chunk)
RETURN document.filename, chunk.chunk_number, chunk.text
LIMIT 25;
```

```cypher
MATCH (chunk:Chunk)-[:MENTIONS]->(entity:Entity)
RETURN entity.name, chunk.text
LIMIT 25;
```

Neo4j statuses:

- `connected`: database is reachable.
- `unavailable`: Neo4j is configured but stopped or unreachable.
- `disabled`: no password/connection is configured.

## API reference

### `GET /health`

Returns backend and Neo4j status.

### `POST /documents/upload`

Upload one or more files using the form field `files`.

Example:

```powershell
curl.exe -X POST `
  -F "files=@C:\path\research.pdf" `
  -F "files=@C:\path\notes.txt" `
  http://127.0.0.1:8000/documents/upload
```

Example response:

```json
{
  "message": "Uploaded 1 file(s)",
  "documents": [
    {
      "document_id": "abc123",
      "filename": "research.pdf",
      "file_type": "pdf",
      "chunks": 4
    }
  ],
  "failed": []
}
```

Unsupported, empty, corrupted, and unreadable files are returned in `failed`
without stopping other valid files from being processed.

### `GET /llm`

Ask a question:

```text
http://127.0.0.1:8000/llm?query=What%20is%20the%20main%20idea%3F
```

Restrict the question to selected documents by repeating `document_ids`:

```text
/llm?query=Summarize%20this&document_ids=abc123&document_ids=def456
```

Response fields:

```json
{
  "answer": "Answer from Ollama",
  "sources": [
    {
      "filename": "research.pdf",
      "document_id": "abc123",
      "chunk_number": 1,
      "text": "Retrieved passage...",
      "rank": 1,
      "distance": 0.82,
      "citation": "[Source 1] research.pdf, page 2, chunk 1"
    }
  ],
  "graph_facts": []
}
```

### `GET /ingest`

Reads `.txt` files from `backend/docs/` and indexes them. Normal frontend
uploads should use `/documents/upload`.

## Current limitations

The current prototype does not yet implement the following research-paper
features:

- BM25 keyword search and reciprocal-rank hybrid fusion
- Cross-encoder reranking
- OCR for scanned PDFs or images
- Formal confidence scoring
- Claim-level citation verification
- Full document listing, delete, download, or rename APIs
- User accounts and authentication
- Chat history stored on the backend
- A full Neo4j relationship extraction model
- Automated Precision@5, Recall@5, MRR, latency, or answer-quality evaluation

These should not be claimed as completed until backend support and tests are
added.

## Troubleshooting

### FastAPI does not start

Make sure dependencies are installed and run the command from `backend/`:

```powershell
python -m uvicorn main:app --reload
```

### Ollama error

Start Ollama and make sure the model exists:

```powershell
ollama serve
ollama run llama3.2
```

### Neo4j unavailable

Start the `RAG` database in Neo4j Desktop. Neo4j is optional, so FAISS
document search can still work without it.
