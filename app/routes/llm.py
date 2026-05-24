"""LLM diagnostic endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.dependencies import get_current_user
from app.config import settings
from app.llm import get_llm
from app.models.user import User

router = APIRouter(prefix="/llm", tags=["llm"])


class LLMPingRequest(BaseModel):
    prompt: str = Field(
        default="Reply with exactly: pong",
        min_length=1,
        max_length=500,
        description="Prompt sent to the configured LLM provider.",
    )


class LLMPingResponse(BaseModel):
    provider: str
    model: str
    prompt: str
    response: str


class LLMStatusResponse(BaseModel):
    provider: str
    model: str
    endpoint: str
    note: str


@router.get("/status", response_model=LLMStatusResponse)
async def llm_status(_: User = Depends(get_current_user)) -> LLMStatusResponse:
    """Report which LLM provider is currently configured.

    Does NOT make a network call to the provider — purely reads config.
    Use /llm/ping to verify the provider is actually reachable.
    """
    if settings.llm_provider.lower() == "ollama":
        endpoint = settings.ollama_base_url
        model = settings.llm_model
    elif settings.llm_provider.lower() == "bedrock":
        endpoint = f"bedrock-runtime.{settings.aws_region}.amazonaws.com"
        model = settings.bedrock_model_id
    else:
        endpoint = "unknown"
        model = "unknown"

    return LLMStatusResponse(
        provider=settings.llm_provider,
        model=model,
        endpoint=endpoint,
        note="Switch providers by changing LLM_PROVIDER in .env and restarting the API.",
    )


@router.post("/ping", response_model=LLMPingResponse)
async def llm_ping(
    payload: LLMPingRequest,
    _: User = Depends(get_current_user),
) -> LLMPingResponse:
    """Send a prompt to the configured LLM and return its response.

    Proves the abstraction works end-to-end: same endpoint code, different
    provider depending on LLM_PROVIDER env var.
    """
    llm = get_llm()
    try:
        result = await llm.ainvoke(payload.prompt)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM provider '{settings.llm_provider}' unreachable: {exc}",
        ) from exc

    # Ollama returns str; Bedrock chat models return AIMessage with .content.
    response_text = result if isinstance(result, str) else getattr(result, "content", str(result))

    if settings.llm_provider.lower() == "ollama":
        model = settings.llm_model
    else:
        model = settings.bedrock_model_id

    return LLMPingResponse(
        provider=settings.llm_provider,
        model=model,
        prompt=payload.prompt,
        response=response_text,
    )