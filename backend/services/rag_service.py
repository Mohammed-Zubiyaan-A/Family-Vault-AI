"""
Embeddings + retrieval for cross-document Q&A (ARCHITECTURE.md 'RAG
(retrieval)'). Every answer must include a source document reference —
that's enforced in the QA router, not here, but this module supplies the
chunks the answer is grounded in.
"""
from __future__ import annotations

from sentence_transformers import SentenceTransformer
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.config import get_settings
from db.models import Document, DocumentChunk
from services.llm_client import get_llm_client

_model: SentenceTransformer | None = None


def _get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(get_settings().EMBEDDING_MODEL)
    return _model


def embed_text(text: str) -> list[float]:
    model = _get_embedding_model()
    return model.encode(text, normalize_embeddings=True).tolist()


def embed_and_store_chunks(db: Session, document_id: str, document_type: str, chunks: list[str]) -> None:
    model = _get_embedding_model()
    embeddings = model.encode(chunks, normalize_embeddings=True)

    for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
        db.add(
            DocumentChunk(
                document_id=document_id,
                document_type=document_type,
                chunk_index=idx,
                text=chunk_text,
                embedding=embedding.tolist(),
            )
        )
    db.commit()


def retrieve_top_chunks(db: Session, question: str, *, top_k: int = 5) -> list[DocumentChunk]:
    query_embedding = embed_text(question)
    stmt = (
        select(DocumentChunk)
        .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
        .limit(top_k)
    )
    return list(db.execute(stmt).scalars())


_QA_SYSTEM_PROMPT = (
    "Answer the user's question using ONLY the document excerpts "
    "provided below. If the excerpts don't contain the answer, say so "
    "plainly rather than guessing. Be concise."
)


def answer_question(db: Session, question: str) -> tuple[str, list[Document]]:
    chunks = retrieve_top_chunks(db, question)

    if not chunks:
        return "I don't have any documents to answer that from yet.", []

    context = "\n\n---\n\n".join(
        f"[Document: {c.document_id}]\n{c.text}" for c in chunks
    )
    prompt = f"Document excerpts:\n\n{context}\n\nQuestion: {question}"

    llm = get_llm_client()
    answer = llm.generate(prompt, system=_QA_SYSTEM_PROMPT)

    seen_ids = set()
    source_documents: list[Document] = []
    for chunk in chunks:
        if chunk.document_id in seen_ids:
            continue
        seen_ids.add(chunk.document_id)
        doc = db.get(Document, chunk.document_id)
        if doc:
            source_documents.append(doc)

    return answer, source_documents
