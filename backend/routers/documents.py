from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from core.config import get_settings
from db.database import get_db
from db.models import AuditLogEntry, Document, DocumentFact
from models.schemas import (
    ConfirmExtractionRequest,
    ConfirmExtractionResponse,
    DeleteDocumentResponse,
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentStatusResponse,
    DocumentSummary,
    ProcessingStatus,
    UploadResponse,
)
from services import audit_service, extraction_service, ocr_service, rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

# Simple in-process stores for state that doesn't need its own DB table
# for an MVP. Fine for a single-instance backend; move to real columns
# if you ever run more than one worker.
_PENDING_EXTRACTIONS: dict[str, dict] = {}
_STAGE: dict[str, str] = {}


def _extract_key_date(fields: dict) -> str | None:
    return fields.get("agreement_expiry") or fields.get("expiry_date") or fields.get("next_important_date")


def _get_pending_fields(db: Session, document_id: str) -> dict | None:
    """
    The fields the model extracted for a document. Served from memory when
    available; otherwise recovered from the append-only audit log, so a
    document that still needs review can be reviewed later (even after a
    backend restart) instead of the extraction being lost.
    """
    cached = _PENDING_EXTRACTIONS.get(document_id)
    if cached is not None:
        return cached

    entry = (
        db.query(AuditLogEntry)
        .filter_by(document_id=document_id, action="extract")
        .order_by(AuditLogEntry.created_at.desc())
        .first()
    )
    if entry and isinstance(entry.detail, dict):
        return entry.detail.get("fields")
    return None


def _save_fact(db: Session, document_id: str, fields: dict) -> None:
    """Upsert: update the existing fact if one's already there (e.g. the
    user edits a previously auto-saved document), otherwise create it."""
    existing = db.query(DocumentFact).filter_by(document_id=document_id).one_or_none()
    key_date = _extract_key_date(fields)
    if existing:
        existing.fields = fields
        existing.key_date = key_date
    else:
        db.add(DocumentFact(document_id=document_id, fields=fields, key_date=key_date))
    db.commit()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> UploadResponse:
    settings = get_settings()
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    document_id = str(uuid.uuid4())
    suffix = Path(file.filename or "upload").suffix
    saved_path = upload_dir / f"{document_id}{suffix}"

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")
    saved_path.write_bytes(contents)

    document = Document(
        id=document_id,
        filename=file.filename or saved_path.name,
        document_type="unknown",
        status=ProcessingStatus.processing.value,
    )
    db.add(document)
    db.commit()

    _STAGE[document_id] = "queued"
    background_tasks.add_task(_process_document, document_id, str(saved_path))

    return UploadResponse(document_id=document_id, status=ProcessingStatus.processing)


def _process_document(document_id: str, file_path: str) -> None:
    """
    Runs in the background: OCR -> classify -> explain -> extract -> (mark
    ready) -> chunk+embed for RAG.

    IMPORTANT: the explanation + structured fields are what the user is
    waiting to see, and don't depend on embedding at all (embedding only
    feeds cross-document Q&A). So we mark the document "ready" and stash
    the extracted fields for /status to return as soon as extraction is
    done -- embedding happens afterward, in its own try/except, so a
    slow or failed embedding step never blocks or breaks the main result.
    """
    from db.database import SessionLocal  # local import: background task, own session

    db = SessionLocal()
    document = None
    document_type = None
    cleaned_text = ""
    try:
        document = db.get(Document, document_id)
        if document is None:
            logger.error("Document %s vanished before processing", document_id)
            return

        _STAGE[document_id] = "reading document (OCR)"
        raw_text = ocr_service.extract_text(file_path)
        cleaned_text = ocr_service.clean_text(raw_text)

        _STAGE[document_id] = "classifying document type"
        document_type = extraction_service.classify_document_type(cleaned_text)

        _STAGE[document_id] = "writing plain-English explanation"
        explanation = extraction_service.generate_explanation(cleaned_text)

        _STAGE[document_id] = "extracting structured fields"
        extracted_fields = extraction_service.extract_structured_fields(cleaned_text, document_type)

        # Only ask the user to review when extraction is actually
        # incomplete/ambiguous -- if every field came back filled in,
        # save it automatically instead of interrupting them.
        # Done BEFORE marking the document "ready", so the frontend can
        # never observe a ready-but-not-yet-saved state and flash the
        # review form for a document that's about to be auto-saved.
        auto_confirm = extraction_service.fields_are_complete(extracted_fields)
        if auto_confirm:
            _save_fact(db, document_id, extracted_fields)

        document.raw_text = cleaned_text
        document.document_type = document_type.value
        document.explanation = explanation
        document.error_message = None

        # Visible to /status as soon as it's ready -- before embedding.
        _PENDING_EXTRACTIONS[document_id] = extracted_fields
        document.status = ProcessingStatus.ready.value
        db.commit()
        _STAGE.pop(document_id, None)

        audit_service.log(
            db,
            action="extract",
            document_id=document_id,
            detail={"document_type": document_type.value, "fields": extracted_fields},
        )
        if auto_confirm:
            audit_service.log(
                db,
                action="confirm_extraction",
                document_id=document_id,
                detail={"fields": extracted_fields, "auto": True},
                user_approved=False,  # auto-confirmed, not a human approval
            )

    except Exception as exc:  # noqa: BLE001 - catches LLMError and anything else; want any failure surfaced to the user
        logger.exception("Processing failed for document %s", document_id)
        _STAGE.pop(document_id, None)
        if document is not None:
            document.status = ProcessingStatus.error.value
            document.error_message = str(exc)
            db.commit()
        db.close()
        return

    # Embedding is separate: it only feeds cross-document Q&A, so its
    # failure shouldn't flip a successfully-extracted document to "error".
    try:
        chunks = ocr_service.chunk_text(cleaned_text)
        rag_service.embed_and_store_chunks(db, document_id, document_type.value, chunks)
    except Exception:  # noqa: BLE001
        logger.exception(
            "Embedding failed for document %s -- explanation/fields are still saved, "
            "but this document won't be searchable via Q&A until re-processed.",
            document_id,
        )
        audit_service.log(
            db,
            action="embedding_failed",
            document_id=document_id,
            detail={"note": "document saved; Q&A indexing incomplete"},
        )
    finally:
        db.close()


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
def get_document_status(document_id: str, db: Session = Depends(get_db)) -> DocumentStatusResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    fields = document.fact.fields if document.fact else _get_pending_fields(db, document_id)

    return DocumentStatusResponse(
        status=ProcessingStatus(document.status),
        stage=_STAGE.get(document_id),
        explanation=document.explanation,
        extracted_fields=fields,
        error_message=document.error_message,
        confirmed=document.fact is not None,
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document_detail(document_id: str, db: Session = Depends(get_db)) -> DocumentDetailResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    fields = document.fact.fields if document.fact else _get_pending_fields(db, document_id)

    return DocumentDetailResponse(
        document_id=document.id,
        filename=document.filename,
        document_type=document.document_type if document.document_type != "unknown" else "rent_agreement",
        status=ProcessingStatus(document.status),
        explanation=document.explanation,
        fields=fields,
        confirmed=document.fact is not None,
        error_message=document.error_message,
    )


@router.post("/{document_id}/confirm", response_model=ConfirmExtractionResponse)
def confirm_extraction(
    document_id: str,
    body: ConfirmExtractionRequest,
    db: Session = Depends(get_db),
) -> ConfirmExtractionResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    _save_fact(db, document_id, body.fields)
    document.document_type = body.document_type.value
    db.commit()

    audit_service.log(
        db,
        action="confirm_extraction",
        document_id=document_id,
        detail={"fields": body.fields},
        user_approved=True,
    )

    _PENDING_EXTRACTIONS.pop(document_id, None)
    return ConfirmExtractionResponse(document_id=document_id, saved=True)


@router.delete("/{document_id}", response_model=DeleteDocumentResponse)
def delete_document(document_id: str, db: Session = Depends(get_db)) -> DeleteDocumentResponse:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = document.filename

    # Best-effort cleanup of the uploaded file on disk. Not fatal if it's
    # already gone -- the DB rows are the source of truth for the app.
    try:
        settings = get_settings()
        suffix = Path(filename).suffix
        file_path = Path(settings.UPLOAD_DIR) / f"{document_id}{suffix}"
        file_path.unlink(missing_ok=True)
    except OSError:
        logger.warning("Could not remove uploaded file for document %s", document_id, exc_info=True)

    db.delete(document)  # cascades to DocumentFact + DocumentChunk rows
    db.commit()

    _PENDING_EXTRACTIONS.pop(document_id, None)
    _STAGE.pop(document_id, None)

    audit_service.log(db, action="delete_document", document_id=document_id, detail={"filename": filename})

    return DeleteDocumentResponse(document_id=document_id, deleted=True)


@router.get("", response_model=DocumentListResponse)
def list_documents(db: Session = Depends(get_db)) -> DocumentListResponse:
    documents = db.query(Document).order_by(Document.created_at.desc()).all()

    summaries = []
    for doc in documents:
        key_dates = []
        if doc.fact and doc.fact.key_date:
            key_dates.append(doc.fact.key_date)

        summaries.append(
            DocumentSummary(
                document_id=doc.id,
                document_type=doc.document_type if doc.document_type != "unknown" else "rent_agreement",
                filename=doc.filename,
                key_dates=key_dates,
                summary=doc.explanation[:200] if doc.explanation else None,
                status=ProcessingStatus(doc.status),
                confirmed=doc.fact is not None,
            )
        )

    return DocumentListResponse(documents=summaries)
