"""
MIRA Stylist — Voice / Speaking Stylist Routes
Optional voice mode for a more personal, immersive experience.
"""

from fastapi import APIRouter, UploadFile, File
from ..models.schemas import VoiceRequest, VoiceResponse, APIResponse
from ..services.voice_service import VoiceService

router = APIRouter(prefix="/api/voice", tags=["Voice"])
voice_service = VoiceService()


@router.post("/synthesize", response_model=APIResponse)
async def synthesize_speech(request: VoiceRequest):
    """Generate speech audio from text in MIRA's voice (Cartesia Sonic)."""
    try:
        result = await voice_service.synthesize(request)
        return APIResponse(
            success=True,
            data=result.model_dump(mode="json"),
            message="Audio ready.",
        )
    except ValueError as e:
        return APIResponse(
            success=False,
            message=str(e),
        )


@router.get("/welcome", response_model=APIResponse)
async def welcome_message(user_name: str = None):
    """Generate a warm, personalised welcome voice message.

    Uses USER_NAME from settings when no query parameter is provided.
    """
    try:
        result = await voice_service.generate_welcome(user_name)
        return APIResponse(
            success=True,
            data=result.model_dump(mode="json"),
            message="Welcome.",
        )
    except ValueError as e:
        return APIResponse(
            success=False,
            message=str(e),
        )


@router.post("/narrate", response_model=APIResponse)
async def narrate_commentary(commentary_text: str):
    """Narrate stylist commentary in MIRA's voice."""
    try:
        result = await voice_service.narrate_commentary(commentary_text)
        return APIResponse(
            success=True,
            data=result.model_dump(mode="json"),
            message="Commentary narrated.",
        )
    except ValueError as e:
        return APIResponse(
            success=False,
            message=str(e),
        )


@router.post("/transcribe", response_model=APIResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """Transcribe uploaded audio to text using OpenAI Whisper.

    Accepts any audio format supported by the Whisper API
    (webm, mp3, wav, m4a, ogg, etc.).
    """
    try:
        audio_bytes = await file.read()
        import io
        text = await voice_service.transcribe(
            io.BytesIO(audio_bytes),
            filename=file.filename or "audio.webm",
        )
        return APIResponse(
            success=True,
            data={"text": text},
            message="Transcription complete.",
        )
    except ValueError as e:
        return APIResponse(
            success=False,
            message=str(e),
        )
