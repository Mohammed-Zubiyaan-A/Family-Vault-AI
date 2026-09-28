from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.config import get_settings
from db.database import get_db
from models.schemas import QARequest, QAResponse, QASource
from services import audit_service, rag_service
from services.llm_client import LLMError

router = APIRouter(prefix="/qa", tags=["qa"])


@router.post("/ask", response_model=QAResponse)
def ask_question(body: QARequest, db: Session = Depends(get_db)) -> QAResponse:
    try:
        answer, source_documents = rag_service.answer_question(db, body.question)
    except LLMError as exc:
        # Bounded by OLLAMA_TIMEOUT_SECONDS -- this fires instead of hanging
        # forever, so the frontend gets a real error instead of an endless
        # "Thinking..." state.
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - e.g. embedding-model errors
        raise HTTPException(status_code=500, detail=f"Couldn't answer that: {exc}") from exc

    sources = [
        QASource(document_id=doc.id, filename=doc.filename) for doc in source_documents
    ]

    audit_service.log(
        db,
        action="qa_answer",
        detail={"question": body.question, "answer": answer, "source_ids": [d.id for d in source_documents]},
    )

    return QAResponse(answer=answer, sources=sources, ollama_mode=get_settings().OLLAMA_MODE)
