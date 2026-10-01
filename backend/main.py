from pathlib import Path
import uuid

import httpx
import fitz
import ollama
from docx.opc.exceptions import PackageNotFoundError
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from graph_service import save_document as save_graph_document, search_graph
from graph_service import graph_status
from services.document_service import (
    doc_extract,
    load_texts,
    pdf_extract,
    save_document,
    save_texts,
    search_documents,
    split_text,
    txt_extract,
)

app = FastAPI(title="Document-aware RAG Assistant")
ollama_client = ollama.Client(timeout=60)

ROOT = Path(__file__).resolve().parent

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "backend": "ok",
        "neo4j": graph_status(),
    }


@app.post("/documents/upload")
async def upload_documents(files: list[UploadFile] = File(...)):

    documents_uploaded = []
    failed = []
    (ROOT / "uploads").mkdir(exist_ok=True)

    for file in files:
        suffix = Path(file.filename or "").suffix.lower()

        if suffix not in (".pdf", ".txt", ".docx"):
            failed.append({
                "filename": file.filename or "unknown file",
                "error": "Only PDF, TXT, and DOCX files are supported.",
            })
            continue

        saved_file = ROOT / "uploads" / f"{uuid.uuid4().hex}{suffix}"

        try:
            saved_file.write_bytes(await file.read())

            if suffix == ".pdf":
                pages = pdf_extract(saved_file)
            elif suffix == ".txt":
                pages = txt_extract(saved_file)
            else:
                pages = doc_extract(saved_file)

            document_info = save_document(pages, file.filename or "document", suffix[1:])
            save_graph_document(document_info, pages)
            documents_uploaded.append(document_info)
        except (OSError, ValueError, UnicodeError, fitz.FileDataError, PackageNotFoundError) as error:
            failed.append({
                "filename": file.filename or "unknown file",
                "error": str(error),
            })
        finally:
            await file.close()

    return {
        "message": f"Uploaded {len(documents_uploaded)} file(s)",
        "documents": documents_uploaded,
        "failed": failed,
    }


@app.get("/ingest")
def ingest():
    texts = []
    document_ids = set()
    docs_folder = ROOT / "docs"
    docs_folder.mkdir(exist_ok=True)

    for path in docs_folder.iterdir():
        if path.is_file() and path.suffix.lower() == ".txt":
            text = path.read_text(encoding="utf-8").strip()
            if text:
                document_id = uuid.uuid5(uuid.NAMESPACE_URL, str(path.resolve())).hex
                document_ids.add(document_id)
                for chunk_number, chunk in enumerate(split_text(text), 1):
                    texts.append({
                        "text": chunk,
                        "document_id": document_id,
                        "filename": path.name,
                        "file_type": "txt",
                        "chunk_number": chunk_number,
                    })

    if not texts:
        return {"message": "No documents found"}

    existing_texts = [
        item for item in load_texts()
        if item.get("document_id") not in document_ids
    ]
    save_texts(existing_texts + texts)

    return {"message": "Ingested Successfully", "documents": len(document_ids)}


@app.get("/llm")
def llm(
    query: str = Query(min_length=1, description="Question about the uploaded files"),
    document_ids: list[str] = Query(default=[]),
):
    query = query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Please enter a question.")

    records = search_documents(query, document_ids)
    graph_records = search_graph(query, document_ids)
    if not records:
        return {"answer": "No relevant documents found.", "sources": [], "graph_facts": []}

    context = "\n\n".join(
        f"[Source {record['rank']}: {record.get('filename', 'document')}"
        f"{f', page {record['page']}' if record.get('page') else ''}]\n"
        f"{record['text']}"
        for record in records
    )
    graph_context = "\n".join(
        f"- {item['name']} appears in {item['filename']}"
        f"{f', page {item['page']}' if item.get('page') else ''}"
        for item in graph_records
    )

    prompt = f"""You are a Senior Consultant.

Answer using the retrieved document context as the primary source.
Use [Source N] citations in your answer when making factual claims.
Do not invent source numbers. If the sources do not answer the question, say:
"I don't have enough information in the provided documents."

Retrieved document context:
{context}

Knowledge graph facts:
{graph_context or "No matching graph facts found."}

Question:
{query}

Answer:
"""
    try:
        response = ollama_client.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
            options={"num_predict": 256},
        )
    except ConnectionError as error:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Start it with: ollama serve",
        ) from error
    except httpx.ReadTimeout as error:
        raise HTTPException(
            status_code=504,
            detail="Ollama took too long to answer. Check that llama3.2 is running.",
        ) from error
    except httpx.ConnectError as error:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Start it with: ollama serve",
        ) from error
    except ollama.ResponseError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    return {
        "answer": response["message"]["content"],
        "sources": records,
        "graph_facts": graph_records,
    }
