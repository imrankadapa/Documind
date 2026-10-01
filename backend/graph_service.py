import os
import re

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable

from services.document_service import split_text


URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "")
DATABASE = os.getenv("NEO4J_DATABASE", "RAG")

driver = (
    GraphDatabase.driver(
        URI,
        auth=(USERNAME, PASSWORD),
        connection_timeout=1,
        max_transaction_retry_time=0,
    )
    if PASSWORD
    else None
)

COMMON_WORDS = {
    "The",
    "This",
    "That",
    "When",
    "What",
    "Where",
    "How",
    "And",
    "Using",
    "From",
    "With",
    "Into",
    "About",
    "After",
    "Before",
    "Between",
    "During",
    "Without",
    "Their",
    "There",
    "These",
    "Those",
}


def graph_status():
    if driver is None:
        return "disabled"

    try:
        driver.verify_connectivity()
        return "connected"
    except (Neo4jError, ServiceUnavailable):
        return "unavailable"


def find_entities(text):
    names = re.findall(r"\b[A-Z][A-Za-z0-9-]*(?:\s+[A-Z][A-Za-z0-9-]*)+\b", text)
    names += re.findall(r"\b[A-Z][A-Za-z0-9-]{2,}\b", text)

    clean = []
    for name in names:
        if name.strip() and name not in COMMON_WORDS:
            clean.append(name.strip())

    return list(dict.fromkeys(clean))[:20]


def save_document(info, pages):
    if driver is None:
        return

    try:
        with driver.session(database=DATABASE) as session:
            session.execute_write(_save_document, info, pages)
    except (Neo4jError, ServiceUnavailable):
        return


def _save_document(tx, info, pages):
    tx.run(
        """
        MERGE (document:Document {document_id: $document_id})
        SET document.filename = $filename,
            document.file_type = $file_type
        """,
        **info,
    )

    chunk_number = 0
    for page in pages:
        text = page["text"]
        for part in split_text(text):
            chunk_number += 1
            chunk_id = f"{info['document_id']}-{chunk_number}"
            tx.run(
                """
                MATCH (document:Document {document_id: $document_id})
                MERGE (chunk:Chunk {chunk_id: $chunk_id})
                SET chunk.text = $text,
                    chunk.page = $page,
                    chunk.chunk_number = $chunk_number
                MERGE (document)-[:HAS_CHUNK]->(chunk)
                """,
                document_id=info["document_id"],
                chunk_id=chunk_id,
                text=part.strip(),
                page=page.get("page"),
                chunk_number=chunk_number,
            )

            entities = find_entities(part)
            for name in entities:
                tx.run(
                    """
                    MATCH (document:Document {document_id: $document_id})
                    MATCH (chunk:Chunk {chunk_id: $chunk_id})
                    MERGE (entity:Entity {name: $name})
                    MERGE (document)-[:MENTIONS]->(entity)
                    MERGE (chunk)-[:MENTIONS]->(entity)
                    """,
                    document_id=info["document_id"],
                    chunk_id=chunk_id,
                    name=name,
                )


def search_graph(question, document_ids=None):
    if driver is None:
        return []

    words = find_entities(question)
    if not words:
        return []

    try:
        with driver.session(database=DATABASE) as session:
            result = session.run(
                """
                MATCH (document:Document)-[:HAS_CHUNK]->(chunk:Chunk)-[:MENTIONS]->(entity:Entity)
                WHERE entity.name IN $words
                  AND ($document_ids = [] OR document.document_id IN $document_ids)
                RETURN entity.name AS name,
                       collect(DISTINCT document.filename) AS filenames,
                       collect(DISTINCT chunk.page) AS pages,
                       collect(DISTINCT document.document_id) AS document_ids,
                       count(DISTINCT chunk) AS chunk_count
                ORDER BY chunk_count DESC
                LIMIT 8
                """,
                words=words,
                document_ids=document_ids or [],
            )

            facts = []
            for record in result:
                file_names = list(dict.fromkeys(record["filenames"] or []))
                pages = [page for page in (record["pages"] or []) if page is not None]
                fact = {
                    "name": record["name"],
                    "filename": file_names[0] if file_names else "document",
                    "page": pages[0] if pages else None,
                    "document_ids": record["document_ids"] or [],
                    "chunk_count": record["chunk_count"],
                }
                fact["reason"] = (
                    f"{fact['name']} appears in {', '.join(file_names[:3])}"
                    + (f" on page {fact['page']}" if fact.get('page') else "")
                )
                facts.append(fact)
            return facts
    except (Neo4jError, ServiceUnavailable):
        return []
