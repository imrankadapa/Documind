# DocuMind: Document Question-Answering System

## 1. Project Overview

DocuMind is a local document question-answering system. A user uploads a PDF,
TXT, or DOCX file from the Streamlit frontend. The FastAPI backend extracts the
text, divides it into chunks, creates sentence embeddings, stores the vectors
in FAISS, and sends the most relevant passages to Ollama for an answer.

The project is intentionally kept simple so that the complete flow is easy to
understand:

```text
Streamlit frontend
        |
        v
FastAPI upload/chat API
        |
        +--> PDF/TXT/DOCX text extraction
        |
        +--> text cleaning and chunking
        |
        +--> Sentence Transformer embeddings
        |
        +--> FAISS similarity search
        |
        +--> Ollama answer generation
```

Neo4j is an optional helper. It stores simple document, chunk, and entity
relationships, but FAISS is the main retrieval system and the application can
run without Neo4j.

This document covers only:

- `backend/`
- `frontend/`

The separate `frontend 2` React/Vite experiment is intentionally excluded.

## 2. Project Objectives

The main objectives are:

1. Allow users to upload multiple supported documents.
2. Extract readable content from PDF, TXT, and DOCX files.
3. Preserve useful metadata such as filename, document ID, file type, page, and
   chunk number.
4. Search uploaded content using semantic similarity.
5. Generate answers using the retrieved document context.
6. Show useful citations and source passages.
7. Keep the system local and easy to run for a student project.
8. Continue working when the optional Neo4j service is unavailable.

## 3. Scope

### Included

- PDF text extraction using PyMuPDF.
- TXT extraction using UTF-8 handling.
- DOCX paragraph and table extraction using `python-docx`.
- Multi-file upload using `multipart/form-data`.
- Unique document IDs.
- Original file storage in `backend/uploads/`.
- Text chunking.
- Sentence Transformer embeddings.
- FAISS vector search.
- Ollama-based answer generation.
- Source metadata and citations.
- Streamlit chat interface.
- Optional Neo4j graph storage and lookup.
- Health endpoint and clear service errors.

### Not included yet

- User accounts and authentication.
- Backend-persisted chat history.
- Delete, rename, and download document APIs.
- OCR for scanned PDFs.
- BM25 plus reciprocal-rank fusion.
- Cross-encoder reranking.
- Formal confidence scoring.
- Automated answer-quality evaluation.
- Full natural-language entity and relationship extraction.

## 4. Existing Project Structure

```text
FastApi/
├── backend/
│   ├── main.py
│   ├── embedding_model.py
│   ├── graph_service.py
│   ├── requirements.txt
│   ├── services/
│   │   └── document_service.py
│   ├── uploads/
│   ├── documents.json
│   ├── texts.npy
│   └── vector.index
├── frontend/
│   ├── frontend.py
│   └── requirements.txt
├── README.md
└── PROJECT_DOCUMENTATION.md
```

Generated files:

- `backend/uploads/`: original uploaded files with generated storage names.
- `backend/documents.json`: document-level metadata.
- `backend/texts.npy`: chunk text and metadata used with FAISS.
- `backend/vector.index`: FAISS vector index.

Generated files should not be edited manually.

## 5. System Architecture and Design

### 5.1 Frontend layer

The Streamlit application in [`frontend/frontend.py`](./frontend/frontend.py)
provides:

- Sidebar file upload.
- Multiple-file selection.
- Backend online/offline status.
- Uploaded document list.
- Chat message history in the current browser session.
- Source expanders for retrieved passages.
- Optional knowledge graph facts.

The frontend sends files to FastAPI and sends questions as query parameters to
the `/llm` endpoint.

### 5.2 API layer

[`backend/main.py`](./backend/main.py) contains the FastAPI application and
keeps the request flow direct:

1. Validate the uploaded filename extension.
2. Save the original file with a UUID-based name.
3. Select the matching extractor.
4. Index extracted chunks.
5. Optionally save graph data.
6. Return successful and failed file results.

For chat:

1. Validate the question.
2. Search FAISS for relevant chunks.
3. Optionally search Neo4j for graph facts.
4. Build a grounded prompt.
5. Call Ollama with the `llama3.2` model.
6. Return the generated answer and source records.

### 5.3 Document processing layer

[`backend/services/document_service.py`](./backend/services/document_service.py)
contains the extraction, chunking, embedding, indexing, metadata, and
retrieval functions.

The extraction functions return a common page-like structure:

```python
{"text": "extracted text", "page": 2}
```

The `page` field is present for PDFs and omitted for TXT and DOCX files when
there is no reliable page information.

### 5.4 Retrieval layer

The retrieval process uses:

- `all-MiniLM-L6-v2` from Sentence Transformers.
- FAISS `IndexFlatL2`.
- Euclidean distance for nearest-neighbor ranking.
- A configurable result count, currently five results for chat.

The search first gets a broader set of candidates and then filters them by the
requested document IDs. This allows a question to be restricted to the files
uploaded in the current frontend session.

### 5.5 Generation layer

The backend creates a prompt containing:

- Retrieved document passages.
- Source numbers.
- Filename and page information when available.
- Optional graph facts.
- Instructions not to invent source numbers.
- A fallback statement when the context does not answer the question.

Ollama generates the final answer locally. Ollama is not required for upload or
FAISS indexing, but it is required for generated chat answers.

## 6. Technologies and Tools Used

### Backend

| Technology | Purpose |
|---|---|
| Python | Main implementation language |
| FastAPI | HTTP API framework |
| Uvicorn | Local ASGI server |
| python-multipart | Multipart upload parsing |
| PyMuPDF (`fitz`) | PDF text extraction |
| `python-docx` | DOCX paragraph and table extraction |
| Sentence Transformers | Text embeddings |
| `all-MiniLM-L6-v2` | Embedding model |
| FAISS | Vector index and similarity search |
| NumPy | Embedding and metadata persistence |
| Ollama | Local language model generation |
| `httpx` | Timeout and connection error handling |
| Neo4j Python driver | Optional graph integration |

### Frontend

| Technology | Purpose |
|---|---|
| Streamlit | Student-friendly web user interface |
| Requests | Calls to the FastAPI backend |
| Custom CSS | Dark theme and chat layout |

### Development tools

- PowerShell on Windows.
- FastAPI interactive documentation at `/docs`.
- Neo4j Browser at `http://localhost:7474` when Neo4j is enabled.
- Local Ollama model `llama3.2`.

## 7. Module-wise Implementation and Progress

| Module | Main file | Status | Details |
|---|---|---|---|
| FastAPI application | `backend/main.py` | Completed | Health, upload, ingest, and chat routes |
| PDF extraction | `document_service.py` | Completed | PyMuPDF extracts readable text per page |
| TXT extraction | `document_service.py` | Completed | UTF-8 and UTF-8 BOM support |
| DOCX extraction | `document_service.py` | Completed | Paragraphs and table rows are extracted |
| Text normalization | `document_service.py` | Completed | Whitespace is normalized before chunking |
| Text chunking | `document_service.py` | Completed | Simple 800-character chunks |
| Embedding generation | `embedding_model.py` | Completed | `all-MiniLM-L6-v2` |
| Vector storage | `document_service.py` | Completed | FAISS plus NumPy metadata |
| Document metadata | `document_service.py` | Completed | UUID, filename, type, chunks |
| Semantic retrieval | `document_service.py` | Completed | FAISS nearest-neighbor search |
| LLM generation | `backend/main.py` | Completed | Ollama `llama3.2` |
| Source citations | Backend and Streamlit | Completed | Rank, filename, page, chunk, distance |
| Streamlit upload UI | `frontend/frontend.py` | Completed | Multiple PDF/TXT/DOCX files |
| Streamlit chat UI | `frontend/frontend.py` | Completed | Session messages and source expanders |
| Health monitoring | Backend and Streamlit | Completed | Backend and optional Neo4j status |
| Neo4j graph helper | `backend/graph_service.py` | Optional | Document, chunk, and entity relationships |
| OCR | Not implemented | Remaining | Scanned image PDFs are not read |
| Hybrid BM25 retrieval | Not implemented | Remaining | Current retrieval is FAISS-only |
| Reranking | Not implemented | Remaining | No cross-encoder stage |
| Evaluation metrics | Not implemented | Remaining | No Precision@5, Recall, MRR, or latency suite |
| Document management APIs | Not implemented | Remaining | No list/delete/download/rename routes |

## 8. Database, API, and System Integration

### 8.1 File storage

Original files are stored in:

```text
backend/uploads/
```

The stored filename is generated with `uuid.uuid4().hex`, so two uploaded
files with the same original name do not overwrite each other. The original
filename remains in metadata for display and citation.

### 8.2 Metadata storage

`documents.json` stores document-level records:

```json
{
  "document_id": "generated-id",
  "filename": "research.pdf",
  "file_type": "pdf",
  "chunks": 12
}
```

`texts.npy` stores chunk-level dictionaries, including:

- `text`
- `document_id`
- `filename`
- `file_type`
- `chunk_number`
- optional `page`

### 8.3 API endpoints

#### `GET /health`

Returns backend and Neo4j status.

Example:

```json
{
  "backend": "ok",
  "neo4j": "unavailable"
}
```

#### `POST /documents/upload`

Accepts one or more files under the multipart field `files`.

```powershell
curl.exe -X POST `
  -F "files=@C:\documents\research.pdf" `
  -F "files=@C:\documents\notes.txt" `
  http://127.0.0.1:8000/documents/upload
```

The response separates successful and failed files:

```json
{
  "message": "Uploaded 1 file(s)",
  "documents": [
    {
      "document_id": "abc123",
      "filename": "research.pdf",
      "file_type": "pdf",
      "chunks": 8
    }
  ],
  "failed": []
}
```

#### `GET /llm`

Required parameter:

```text
query
```

Optional repeated parameter:

```text
document_ids
```

Example:

```text
/llm?query=What%20is%20the%20main%20idea%3F&document_ids=abc123
```

The response includes:

- `answer`
- `sources`
- `graph_facts`

#### `GET /ingest`

Reads `.txt` files from `backend/docs/` and indexes them. Normal frontend
uploads should use `/documents/upload`.

### 8.4 Optional Neo4j integration

The graph helper uses:

```text
(Document)-[:HAS_CHUNK]->(Chunk)-[:MENTIONS]->(Entity)
```

Neo4j settings are read from:

- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE`

The default test values are:

```text
URI: neo4j://127.0.0.1:7687
Username: neo4j
Database: RAG
```

If Neo4j is stopped, the API reports it as unavailable and the FAISS flow
continues. Graph failures do not replace the main document retrieval path.

### 8.5 Ollama integration

The backend uses the local `llama3.2` model. It handles:

- Ollama not running: HTTP 503.
- Ollama timeout: HTTP 504.
- Ollama model/API error: HTTP 502.

The user must start Ollama separately:

```powershell
ollama serve
ollama run llama3.2
```

## 9. Testing Strategy and Test Cases

Testing focuses on the complete upload-to-answer flow and on clear failure
messages.

### 9.1 Static and import checks

```powershell
cd C:\Users\kadap\Pictures\FastApi
python -m compileall backend frontend
```

This checks Python syntax for the FastAPI and Streamlit files.

### 9.2 Backend startup test

```powershell
cd C:\Users\kadap\Pictures\FastApi\backend
python -m uvicorn main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
http://127.0.0.1:8000/health
```

### 9.3 Functional test cases

| ID | Test case | Expected result |
|---|---|---|
| T01 | Start FastAPI | API starts on port 8000 |
| T02 | Open `/health` | Returns backend status |
| T03 | Upload a readable PDF | File is stored, extracted, chunked, and indexed |
| T04 | Upload a UTF-8 TXT file | Text is indexed successfully |
| T05 | Upload a DOCX with paragraphs | Paragraph content is indexed |
| T06 | Upload a DOCX with tables | Table row content is indexed |
| T07 | Upload multiple files | Valid files are processed in one request |
| T08 | Upload `.jpg` or another unsupported type | File appears in `failed` with a useful message |
| T09 | Upload an empty file | File is rejected as unreadable/empty |
| T10 | Upload a corrupted PDF | File is reported as failed |
| T11 | Upload an invalid DOCX | File is reported as failed |
| T12 | Ask a blank question | API returns HTTP 400 |
| T13 | Ask a question with Ollama stopped | API returns HTTP 503 |
| T14 | Ask a question with selected document IDs | Results are restricted to those IDs |
| T15 | Ask a question with no relevant index | Returns no relevant documents |
| T16 | Stop Neo4j and upload a file | Main FAISS flow remains usable |
| T17 | Inspect Streamlit source expander | Filename, rank, passage, and distance appear |

### 9.4 Manual frontend test

```powershell
cd C:\Users\kadap\Pictures\FastApi\frontend
pip install -r requirements.txt
streamlit run frontend.py
```

Open `http://localhost:8501`, upload a document from the sidebar, and ask a
question in the chat input.

## 10. Implementation Results

The implemented baseline provides a working local RAG pipeline:

1. A user selects one or more supported documents.
2. Streamlit sends them to FastAPI as multipart data.
3. FastAPI validates the extension and stores each original file.
4. The matching extractor produces normalized text.
5. Text is divided into chunks.
6. Embeddings are generated with `all-MiniLM-L6-v2`.
7. FAISS is rebuilt with the stored chunk metadata.
8. The question is embedded and matched against the index.
9. Retrieved passages are inserted into the Ollama prompt.
10. The answer and citations are returned to Streamlit.

The implementation was checked with:

- Python compilation of backend and frontend files.
- FastAPI import/startup.
- Vite-independent Streamlit startup.
- Health status request.
- Real TXT upload through the browser.
- Successful document indexing with returned chunk count.
- Offline Neo4j fallback behavior.
- Clear Ollama connection error handling.

## 11. Screenshots

The Streamlit interface was checked at `http://localhost:8501`.

### Screenshot 1: Initial Streamlit screen

The initial screen contains:

- Dark application theme.
- Sidebar document uploader.
- Backend online/offline status.
- Empty uploaded-file area.
- Welcome chat area.
- Chat input at the bottom.

### Screenshot 2: Uploaded document state

After a successful upload, the sidebar displays:

- Original filename.
- Ready status.
- Document count.

The backend response also includes the generated document ID and chunk count.

### Screenshot 3: Answer and source state

After Ollama answers a question, the chat displays the answer. The source
expander displays the retrieved citation, passage text, and FAISS distance.

For a report submission, capture these three states from the running
Streamlit application and place the images in a `screenshots/` folder beside
this document:

```text
screenshots/
├── 01-streamlit-empty.png
├── 02-streamlit-uploaded.png
└── 03-streamlit-answer-sources.png
```

## 12. Error Handling

The backend handles:

- Unsupported file extensions.
- Empty or unreadable documents.
- Invalid DOCX packages.
- Corrupted PDF files.
- UTF-8 text reading errors.
- File-system write errors.
- Missing FAISS index.
- Missing relevant documents.
- Ollama connection failures.
- Ollama timeouts.
- Ollama response errors.
- Neo4j being unavailable.

Upload errors are returned per file so that one invalid file does not prevent
other valid files in the same request from being processed.

## 13. Security and Reliability Notes

This is a local student prototype, not a public production service.

Current protections and reliability choices:

- File extensions are checked before extraction.
- Stored filenames are UUID-based.
- Original filenames are retained only as metadata.
- The upload endpoint does not execute uploaded files.
- CORS is restricted to the local development frontend origins used by the
  project.
- Neo4j is optional and isolated from the FAISS path.
- Service errors are converted into understandable HTTP responses.

Recommended future improvements:

- Add maximum file-size validation.
- Validate MIME types in addition to extensions.
- Add authentication before exposing the API outside localhost.
- Move generated metadata to a real database.
- Add cleanup for failed uploads.
- Add rate limits and request logging.

## 14. How to Run the Complete Backend and Frontend

### Terminal 1: FastAPI

```powershell
cd C:\Users\kadap\Pictures\FastApi\backend
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### Terminal 2: Ollama

```powershell
ollama serve
ollama run llama3.2
```

### Terminal 3: Streamlit

```powershell
cd C:\Users\kadap\Pictures\FastApi\frontend
pip install -r requirements.txt
streamlit run frontend.py
```

Use:

- FastAPI: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`
- Streamlit: `http://localhost:8501`

Neo4j can be started separately, but it is not required for FAISS retrieval or
document uploads.

## 15. Future Work

The next practical improvements should be completed in this order:

1. Add document list, delete, and download endpoints.
2. Add a configured maximum upload size.
3. Add MIME validation and safer temporary-file cleanup.
4. Add OCR for scanned PDFs.
5. Add hybrid FAISS and BM25 retrieval.
6. Add reranking for the top retrieved chunks.
7. Add automated retrieval and answer-quality evaluation.
8. Add formal confidence calculation.
9. Improve Neo4j entity extraction.
10. Add optional user accounts and persistent chat history.

## 16. Conclusion

DocuMind currently works as a local, document-aware RAG prototype. Its main
strength is the simple and understandable flow from Streamlit upload to
FastAPI extraction, FAISS retrieval, and Ollama generation. PDF, TXT, and DOCX
documents are supported, source metadata is preserved, and optional Neo4j
features do not block the main application.

The completed baseline is suitable for demonstrating document upload,
semantic search, grounded question answering, and source citation. Advanced
research features such as hybrid retrieval, reranking, OCR, formal evaluation,
and user management remain future work rather than completed functionality.
