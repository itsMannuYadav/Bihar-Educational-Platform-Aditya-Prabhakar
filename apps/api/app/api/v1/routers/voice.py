from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.ai.providers.stt.base import STTProvider
from app.api.v1.deps import get_stt_provider
from app.core.security import SupabaseClaims, get_current_claims

router = APIRouter(prefix="/voice", tags=["voice"])

_MAX_BYTES = 25 * 1024 * 1024  # 25 MB — Whisper's limit


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str | None = Query(None, description="Language hint: en | hi | hinglish"),
    _claims: SupabaseClaims = Depends(get_current_claims),
    stt: STTProvider = Depends(get_stt_provider),
) -> dict[str, str]:
    content_type = file.content_type or ""
    if content_type and not content_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be an audio upload (audio/*)",
        )

    audio_bytes = await file.read()
    if not audio_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Audio file is empty",
        )
    if len(audio_bytes) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file exceeds {_MAX_BYTES // (1024 * 1024)} MB limit",
        )

    text = await stt.transcribe(
        audio_bytes,
        mime_type=content_type or "audio/webm",
        language_hint=language,
    )
    return {"text": text}
