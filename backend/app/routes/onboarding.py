import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks
from ..models.schemas import (
    OnboardingQuestion, OnboardingResponse,
    UserProfile, APIResponse, QuestionType, LuxuryPreference
)
from ..services.profile_service import ProfileService
from ..utils.env import get_settings

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])
profile_service = ProfileService()
logger = logging.getLogger(__name__)

NARRATIVE_IMMEDIATE_TIMEOUT_SECONDS = 5.5

# Pre-defined onboarding questions — conversational, not form-like
ONBOARDING_QUESTIONS = [
    OnboardingQuestion(
        question_id="name",
        question_text="What should MIRA call you?",
        options=[],
        question_type=QuestionType.FREE_TEXT
    ),
    OnboardingQuestion(
        question_id="gender",
        question_text="Which gender context should MIRA keep in mind?",
        options=["Female", "Male", "Non-binary", "Prefer not to say"],
        question_type=QuestionType.SINGLE_SELECT
    ),
    OnboardingQuestion(
        question_id="aesthetic",
        question_text="Which feels most like you: effortless, sculpted, romantic, sharp, minimal, or dramatic?",
        options=["Effortless", "Sculpted", "Romantic", "Sharp", "Minimal", "Dramatic"],
        question_type=QuestionType.SINGLE_SELECT
    ),
    OnboardingQuestion(
        question_id="silhouette",
        question_text="Do you usually like your clothes to skim the body, define the waist, or fall away more fluidly?",
        options=["Skim the body", "Define the waist", "Fall away fluidly", "It depends on the occasion"],
        question_type=QuestionType.SINGLE_SELECT
    ),
    OnboardingQuestion(
        question_id="dressing_for",
        question_text="Are you dressing more for confidence, elegance, playfulness, power, or ease?",
        options=["Confidence", "Elegance", "Playfulness", "Power", "Ease"],
        question_type=QuestionType.MULTI_SELECT
    ),
    OnboardingQuestion(
        question_id="colors_love",
        question_text="What colours make you feel most like yourself?",
        options=["Rich jewel tones", "Soft neutrals", "Bold brights", "Earth tones", "Pastels", "Monochromes", "Metallics"],
        question_type=QuestionType.MULTI_SELECT
    ),
    OnboardingQuestion(
        question_id="colors_avoid",
        question_text="Are there any colours you tend to shy away from?",
        options=[],
        question_type=QuestionType.FREE_TEXT
    ),
    OnboardingQuestion(
        question_id="occasions",
        question_text="What are you most often dressing for?",
        options=["Work", "Evenings out", "Weddings & celebrations", "Festive occasions", "Everyday elevated", "Travel", "Date nights", "Special events"],
        question_type=QuestionType.MULTI_SELECT
    ),
    OnboardingQuestion(
        question_id="comfort_statement",
        question_text="On a given day, do you lean more toward comfort or making a statement?",
        options=["Mostly comfort", "Slightly comfort", "Balance of both", "Slightly statement", "Mostly statement"],
        question_type=QuestionType.SINGLE_SELECT
    ),
    OnboardingQuestion(
        question_id="modesty",
        question_text="Do you have any modesty or coverage preferences we should keep in mind?",
        options=["Full coverage preferred", "Moderate coverage", "No specific preference", "I'll specify per occasion"],
        question_type=QuestionType.SINGLE_SELECT
    ),
    OnboardingQuestion(
        question_id="luxury_preference",
        question_text="Where does your wardrobe tend to live?",
        options=["Luxury / designer", "Contemporary / premium", "High street / accessible", "A thoughtful mix"],
        question_type=QuestionType.SINGLE_SELECT
    ),
    OnboardingQuestion(
        question_id="style_goal",
        question_text="If MIRA could help you with one thing, what would it be?",
        options=[],
        question_type=QuestionType.FREE_TEXT
    ),
]

@router.get("/questions", response_model=APIResponse)
async def get_onboarding_questions():
    """Return the onboarding question set."""
    return APIResponse(success=True, data=ONBOARDING_QUESTIONS, message="Your style journey begins here.")

@router.post("/submit", response_model=APIResponse)
async def submit_onboarding(
    responses: list[OnboardingResponse],
    background_tasks: BackgroundTasks,
):
    """Process onboarding responses and generate a user profile."""
    profile_data = _build_profile_from_responses(responses)
    narrative_pending = False

    try:
        profile_data["narrative_summary"] = await asyncio.wait_for(
            _generate_narrative(profile_data, responses),
            timeout=NARRATIVE_IMMEDIATE_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        narrative_pending = True
    except Exception:
        logger.exception("Immediate onboarding narrative generation failed.")
        narrative_pending = True

    profile = UserProfile(**profile_data)
    saved = await profile_service.create_profile(profile)

    if narrative_pending:
        background_tasks.add_task(_generate_and_store_narrative, saved.id, responses)

    return APIResponse(
        success=True,
        data={
            **saved.model_dump(mode="json"),
            "narrative_pending": narrative_pending,
        },
        message=(
            "Welcome to MIRA. Your style profile is ready."
            if not narrative_pending
            else "Welcome to MIRA. Your profile is saved while the written style note is finishing."
        )
    )

def _build_profile_from_responses(responses: list[OnboardingResponse]) -> dict:
    """Convert onboarding responses into profile fields."""
    settings = get_settings()
    data = {
        "name": settings.USER_NAME or "Your Profile",
        "measurements": {},
        "approximate_size_history": {},
        "brand_size_references": [],
    }
    for r in responses:
        if r.question_id == "name":
            name = r.answer if isinstance(r.answer, str) else r.answer[0] if r.answer else ""
            cleaned_name = name.strip() if isinstance(name, str) else ""
            if cleaned_name:
                data["name"] = cleaned_name
        elif r.question_id == "gender":
            gender = r.answer if isinstance(r.answer, str) else r.answer[0] if r.answer else ""
            cleaned_gender = gender.strip() if isinstance(gender, str) else ""
            if cleaned_gender and cleaned_gender != "Prefer not to say":
                data["gender"] = cleaned_gender
        elif r.question_id == "aesthetic":
            data["preferred_aesthetic"] = r.answer if isinstance(r.answer, str) else r.answer[0] if r.answer else None
        elif r.question_id == "silhouette":
            val = r.answer if isinstance(r.answer, str) else r.answer[0] if r.answer else None
            data["preferred_silhouettes"] = [val] if val else []
        elif r.question_id == "dressing_for":
            data["style_goals"] = r.answer if isinstance(r.answer, list) else [r.answer] if r.answer else []
        elif r.question_id == "colors_love":
            data["favorite_colors"] = r.answer if isinstance(r.answer, list) else [r.answer] if r.answer else []
        elif r.question_id == "colors_avoid":
            data["disliked_colors"] = r.answer if isinstance(r.answer, list) else [r.answer] if r.answer else []
        elif r.question_id == "occasions":
            data["occasions"] = r.answer if isinstance(r.answer, list) else [r.answer] if r.answer else []
        elif r.question_id == "comfort_statement":
            mapping = {"Mostly comfort": 0.2, "Slightly comfort": 0.4, "Balance of both": 0.5, "Slightly statement": 0.7, "Mostly statement": 0.9}
            val = r.answer if isinstance(r.answer, str) else r.answer[0] if r.answer else "Balance of both"
            data["comfort_vs_statement"] = mapping.get(val, 0.5)
        elif r.question_id == "modesty":
            data["modesty_preference"] = r.answer if isinstance(r.answer, str) else r.answer[0] if r.answer else None
        elif r.question_id == "luxury_preference":
            val = r.answer if isinstance(r.answer, str) else r.answer[0] if r.answer else None
            luxury_mapping = {
                "Luxury / designer": LuxuryPreference.LUXURY,
                "Contemporary / premium": LuxuryPreference.CONTEMPORARY,
                "High street / accessible": LuxuryPreference.CASUAL,
                "A thoughtful mix": LuxuryPreference.CONTEMPORARY,
            }
            data["luxury_preference"] = luxury_mapping.get(val, LuxuryPreference.CONTEMPORARY)
        elif r.question_id == "style_goal":
            note = r.answer if isinstance(r.answer, str) else r.answer[0] if r.answer else ""
            data["stylist_notes"] = [note] if note else []
    return data

async def _generate_narrative(profile_data: dict, responses: list[OnboardingResponse]) -> str:
    """Use OpenAI to generate an elegant narrative summary of the user's style profile."""
    try:
        import openai
        from ..utils.env import get_settings
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            raise ValueError("No OpenAI API key configured")
        response_text = "\n".join([f"Q: {r.question_id} -> A: {r.answer}" for r in responses])
        profile_context = "\n".join(
            [
                f"Name: {profile_data.get('name') or 'Not provided'}",
                f"Gender: {profile_data.get('gender') or 'Not provided'}",
                f"Pronouns: {profile_data.get('pronouns') or 'Not provided'}",
            ]
        )
        client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        completion = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            max_tokens=140,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are MIRA, an elite AI fashion stylist. Generate a concise, elegant "
                        "narrative summary (2-3 sentences) of this person's style identity based "
                        "on their onboarding responses. Write in third person. Be warm, perceptive, "
                        "and refined. Never use clichés or generic phrases. "
                        "Do not infer gender from fashion context. If explicit pronouns are not provided, "
                        "avoid gendered pronouns and use the person's name, 'they', or 'this profile' instead."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Profile context:\n{profile_context}\n\nOnboarding responses:\n{response_text}",
                },
            ],
        )
        return completion.choices[0].message.content or ""
    except Exception:
        return "A distinctive personal style is beginning to take shape — we look forward to refining it together."


async def _generate_and_store_narrative(
    profile_id: str,
    responses: list[OnboardingResponse],
) -> None:
    """Finish the profile narrative off the critical path when the model runs long."""
    try:
        profile = await profile_service.get_profile(profile_id)
        if profile is None:
            return

        profile_data = profile.model_dump(mode="json")
        narrative = await _generate_narrative(profile_data, responses)
        if narrative:
            await profile_service.update_profile(
                profile_id,
                {"narrative_summary": narrative},
            )
    except Exception:
        logger.exception("Background onboarding narrative generation failed for %s.", profile_id)
