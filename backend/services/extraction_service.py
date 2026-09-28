"""
Runs the extracted document text through the local/cloud LLM to produce:
  1. A plain-English explanation (Hindi is a later stretch toggle, not MVP)
  2. Structured fields matching one of the three schemas in
     models/schemas.py — do not invent new fields ad hoc (AGENTS.md).
"""
from __future__ import annotations

import json
import logging

from models.schemas import (
    DocumentType,
    InsuranceFields,
    LoanAgreementFields,
    RentAgreementFields,
)
from services.llm_client import get_llm_client

logger = logging.getLogger(__name__)

_SCHEMA_BY_TYPE = {
    DocumentType.rent_agreement: RentAgreementFields,
    DocumentType.insurance: InsuranceFields,
    DocumentType.loan_agreement: LoanAgreementFields,
}

_EXPLANATION_SYSTEM_PROMPT = (
    "You explain legal/financial family documents (rent agreements, "
    "insurance policies, loan documents) in plain, simple English a "
    "non-expert can understand. Be concise: cover the key numbers, "
    "dates, and obligations. Do not give legal advice or invent facts "
    "not present in the document."
)

_CLASSIFY_SYSTEM_PROMPT = (
    "Classify the document as exactly one of: rent_agreement, insurance, "
    "loan_agreement. Respond with only that single label, nothing else."
)


def classify_document_type(document_text: str) -> DocumentType:
    llm = get_llm_client()
    raw = llm.generate(document_text[:3000], system=_CLASSIFY_SYSTEM_PROMPT).strip().lower()

    for doc_type in DocumentType:
        if doc_type.value in raw:
            return doc_type

    logger.warning("Could not confidently classify document, defaulting to rent_agreement. Raw: %r", raw)
    return DocumentType.rent_agreement


def generate_explanation(document_text: str) -> str:
    llm = get_llm_client()
    return llm.generate(document_text, system=_EXPLANATION_SYSTEM_PROMPT)


def fields_are_complete(fields: dict) -> bool:
    """
    True only if every field the schema expects (other than document_type)
    came back non-null/non-empty. Used to decide whether the user needs
    to review/confirm the extraction, or whether it's confident enough to
    save automatically -- ask only when there's real ambiguity.
    """
    return all(
        value not in (None, "")
        for key, value in fields.items()
        if key != "document_type"
    )


def extract_structured_fields(document_text: str, document_type: DocumentType) -> dict:
    """
    Returns a dict matching the schema for document_type. Any field the
    LLM can't find should come back as null — the frontend's 'Confirm
    extraction' screen is where the user fills gaps/fixes mistakes, not
    this function.
    """
    schema_cls = _SCHEMA_BY_TYPE[document_type]
    schema_json = json.dumps(schema_cls.model_json_schema(), indent=2)

    system_prompt = (
        "Extract structured fields from the document text below. "
        "Respond with ONLY a JSON object matching this schema exactly "
        "(no extra fields, no commentary). Use null for anything not "
        f"stated in the text.\n\nSchema:\n{schema_json}"
    )

    llm = get_llm_client()
    raw_json = llm.generate_json(document_text, system=system_prompt)

    try:
        parsed = json.loads(raw_json)
    except json.JSONDecodeError:
        logger.error("LLM did not return valid JSON for extraction: %r", raw_json)
        parsed = {}

    # Validate/coerce against the real schema so downstream code always
    # gets a well-shaped dict, even if the LLM was sloppy.
    validated = schema_cls.model_validate({**parsed, "document_type": document_type.value})
    return validated.model_dump(mode="json")
