"""
SQLAlchemy ORM models.

- Document / DocumentFact: the "facts" table from ARCHITECTURE.md
  (confirmed, user-approved structured fields) — separate from raw RAG
  chunks, per the "Memory (persistent facts)" section.
- DocumentChunk: pgvector-backed chunks for RAG retrieval.
- AuditLogEntry: minimal append-only log per ARCHITECTURE.md 'Audit trail'
  — every stored fact, generated answer, and suggested action must log
  which document was used, what was extracted/generated, whether the
  user approved it, and which OLLAMA_MODE was active.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="processing")
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    fact: Mapped["DocumentFact | None"] = relationship(
        back_populates="document", uselist=False, cascade="all, delete-orphan"
    )
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentFact(Base):
    """Confirmed, user-approved structured fields for one document."""
    __tablename__ = "document_facts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False, unique=True)
    fields: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Denormalized for fast "what's expiring soon" lookups without
    # re-parsing the JSON blob per document type.
    key_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    document: Mapped["Document"] = relationship(back_populates="fact")


class DocumentChunk(Base):
    """RAG chunk: ~300-500 token slice of cleaned document text + embedding."""
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False)
    document_type: Mapped[str] = mapped_column(String, nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # BGE-M3 / Nomic Embed both commonly used at 1024 dims — adjust to
    # match whichever embedding model EMBEDDING_MODEL actually loads.
    embedding: Mapped[list[float]] = mapped_column(Vector(1024), nullable=False)

    document: Mapped["Document"] = relationship(back_populates="chunks")


class AuditLogEntry(Base):
    """Append-only. Never update or delete rows here."""
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    document_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "extract", "qa_answer"
    detail: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    user_approved: Mapped[bool | None] = mapped_column(nullable=True)
    ollama_mode: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
