from fastapi import APIRouter

from models.schemas import SystemModeResponse
from services.llm_client import get_llm_client

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/mode", response_model=SystemModeResponse)
def get_mode() -> SystemModeResponse:
    """
    Powers the frontend's persistent 'Running: Local' / 'Running: Cloud'
    badge (ARCHITECTURE.md screen 7) — not optional whenever cloud mode
    might be active in a demo.
    """
    info = get_llm_client().active_mode()
    return SystemModeResponse(ollama_mode=info.mode, model=info.model)
