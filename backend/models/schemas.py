"""
Pydantic models for all request/response bodies (per AGENTS.md
conventions). These must always match the schemas in ARCHITECTURE.md —
do not invent new fields ad hoc.
"""
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    rent_agreement = "rent_agreement"
    insurance = "insurance"
    loan_agreement = "loan_agreement"


class ProcessingStatus(str, Enum):
    processing = "processing"
    ready = "ready"
    error = "error"


# --- Structured extraction schemas (ARCHITECTURE.md) ---

class RentAgreementFields(BaseModel):
    document_type: Literal[DocumentType.rent_agreement] = DocumentType.rent_agreement
    tenant: Optional[str] = None
    owner: Optional[str] = None
    monthly_rent: Optional[float] = None
    security_deposit: Optional[float] = None
    agreement_expiry: Optional[date] = None
    notice_period_months: Optional[int] = None


class InsuranceFields(BaseModel):
    document_type: Literal[DocumentType.insurance] = DocumentType.insurance
    policy_holder: Optional[str] = None
    insured_asset: Optional[str] = None
    provider: Optional[str] = None
    coverage_amount: Optional[float] = None
    expiry_date: Optional[date] = None


class LoanAgreementFields(BaseModel):
    document_type: Literal[DocumentType.loan_agreement] = DocumentType.loan_agreement
    borrower: Optional[str] = None
    loan_amount: Optional[float] = None
    interest_rate_pct: Optional[float] = None
    repayment_period_months: Optional[int] = None
    next_important_date: Optional[date] = None


ExtractedFields = Union[RentAgreementFields, InsuranceFields, LoanAgreementFields]


# --- API contract bodies ---

class UploadResponse(BaseModel):
    document_id: str
    status: ProcessingStatus


class DocumentStatusResponse(BaseModel):
    status: ProcessingStatus
    stage: Optional[str] = None  # e.g. "ocr", "explaining", "extracting", "embedding"
    explanation: Optional[str] = None
    extracted_fields: Optional[dict] = None
    error_message: Optional[str] = None
    # True if extraction was confident enough to save automatically (no
    # missing fields) -- frontend skips the edit form in that case and
    # only asks the user to review when something's actually ambiguous.
    confirmed: bool = False


class ConfirmExtractionRequest(BaseModel):
    document_type: DocumentType
    fields: dict = Field(
        ..., description="Confirmed/edited fields matching the schema for document_type"
    )


class ConfirmExtractionResponse(BaseModel):
    document_id: str
    saved: bool = True


class DeleteDocumentResponse(BaseModel):
    document_id: str
    deleted: bool = True


class DocumentSummary(BaseModel):
    document_id: str
    document_type: DocumentType
    filename: str
    key_dates: list[date] = Field(default_factory=list)
    summary: Optional[str] = None
    status: ProcessingStatus = ProcessingStatus.ready
    confirmed: bool = False  # False = saved extraction still needs the user's review


class DocumentListResponse(BaseModel):
    documents: list[DocumentSummary]


class DocumentDetailResponse(BaseModel):
    document_id: str
    filename: str
    document_type: DocumentType
    status: ProcessingStatus
    explanation: Optional[str] = None
    fields: Optional[dict] = None  # confirmed fields if saved, else the pending extraction
    confirmed: bool = False
    error_message: Optional[str] = None


class QASource(BaseModel):
    document_id: str
    filename: str


class QARequest(BaseModel):
    question: str


class QAResponse(BaseModel):
    answer: str
    sources: list[QASource]
    ollama_mode: Literal["local", "cloud"]  # transparency: which mode answered this


class SystemModeResponse(BaseModel):
    ollama_mode: Literal["local", "cloud"]
    model: str
