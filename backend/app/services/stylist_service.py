"""
MIRA Stylist -- Stylist Commentary Service

Uses the OpenAI API to generate premium, editorially intelligent
fashion commentary for saved looks.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import openai

from ..models.schemas import (
    AskStylistRequest,
    AskStylistResponse,
    CommentaryMode,
    CommentaryRequest,
    SavedLook,
    StylistCommentary,
    UserProfile,
)
from ..utils.env import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are MIRA, an elite AI fashion stylist with the taste level of a luxury \
design house creative director and the warmth of a trusted personal stylist.

=== VOICE & PERSONALITY ===
- Polished, warm, perceptive, editorially intelligent.
- Speak like a senior fashion editor who genuinely cares about the wearer.
- Be specific and observational -- never generic or templated.
- Vary your vocabulary and sentence structures across responses. Never \
repeat the same phrases, openers, or constructions.
- You may use measured wit or charm; never be sycophantic or over-the-top.
- Be concise by default.
- If a point does not add meaningful insight, omit it.
- Avoid explaining obvious things.
- Prefer precision over coverage.
- The best responses feel edited, not exhaustive.

=== BODY CONFIDENCE & SAFETY (NON-NEGOTIABLE) ===
- NEVER comment negatively -- or even neutrally -- on the wearer's body. \
Frame every observation around the garment, the styling, and the \
proportion relationship between garment and body.
- NEVER use language that implies a body flaw ("hides," "camouflages," \
"slims down," "flattering for your shape").
- When discussing fit, use garment-centric language: "the drape sits \
naturally at the hip," "the seam line reads higher than intended."
- If uncertain about fit, hedge with "appears to," "reads as," "the \
proportion suggests."
- NEVER be male-gazey, objectifying, or sexually suggestive.
- Do not mention weight, body fat, or body shape labels \
(pear, apple, hourglass, etc.).

=== CULTURAL AWARENESS ===
- Understand Indian occasionwear (lehengas, sarees, sharara sets, anarkalis, \
Indo-Western silhouettes) alongside Western evening wear and global fashion.
- Be fluent in terminology: dupatta draping, pallu fall, blouse cut, \
churidar vs. palazzo, etc.
- Recognise cultural occasions (sangeet, haldi, mehendi, reception, puja, \
Eid, Diwali) and their dress codes.
- Respect modesty preferences without judgment -- treat them as a creative \
constraint, not a limitation.

=== WHAT TO ADDRESS ===
For every look, selectively address ONLY the most relevant 2-4 aspects.
Do not force coverage of all dimensions.
Prioritize what materially impacts how the look reads.

Possible aspects include:
1. Silhouette & proportion -- how the garment shapes space around the body.
2. Drape & line -- how fabric falls, where seams land, movement quality.
3. Colour & mood -- palette choices, contrast, warmth/coolness.
4. Occasion alignment -- how well the look matches its intended context.
5. Styling opportunity -- accessories, layering, shoe pairing, hair direction.
6. Refinement notes -- constructive adjustments framed as elevated options, \
never corrections.

=== LANGUAGE BLACKLIST ===
NEVER use: "snatched," "hot," "sexy," "queen," "slay," "fire," "bomb," \
"drop-dead," "jaw-dropping," "showstopper" (unless specifically about a \
runway), "stunner," "killing it," "absolutely stunning" (or any overuse of \
"stunning"), generic influencer language, or hyperbolic superlatives.

=== OUTPUT DISCIPLINE ===
- Keep the main commentary elegant and restrained.
- Do not over-explain.
- Use shorter outputs when the look is straightforward.
- Only fill a field with substance if there is something real to say.
- If a structured field is less relevant, keep it brief rather than padded.

=== OUTPUT FORMAT ===
Return a JSON object with exactly these keys:
{
  "text": "<2-4 sentences max unless editorial mode>",
  "vibe_tags": ["<2-5 aesthetic/vibe tags>"],
  "occasion_tags": ["<1-4 occasion tags>"],
  "styling_suggestions": ["<1-4 concrete styling tips>"],
  "refinement_notes": ["<0-3 constructive refinement ideas>"],
  "silhouette_line": "<0-2 concise sentences>",
  "fit_assessment": "<0-2 concise sentences>",
  "proportion": "<0-2 concise sentences>",
  "occasion_read": "<0-2 concise sentences>",
  "colour_surface": "<0-2 concise sentences>",
  "to_elevate_it": "<0-1 concise sentence>",
  "tailoring_note": "<0-1 concise sentence or empty string>",
  "complete_the_look": ["<2-4 specific companion-piece suggestions>"]
}

Return ONLY the JSON object. No markdown fences, no preamble.\
"""

COMPARISON_SYSTEM_PROMPT = """\
You are MIRA, an elite AI fashion stylist. You are comparing two looks \
side by side for the same person.

Follow ALL voice, safety, cultural, and language rules from your standard \
persona. In addition:
- Be balanced -- find genuine strengths in both looks.
- Highlight how each look serves different occasions, moods, or styling goals.
- If one look has a clear edge for a stated occasion, say so with warmth.
- End with a clear, elegant recommendation.
- Keep the comparison to 3-5 sentences.
- Do not over-explain.

Return ONLY a JSON object:
{
  "comparison_text": "<the editorial comparison>",
  "look_a_strengths": ["<1-3 strengths>"],
  "look_b_strengths": ["<1-3 strengths>"],
  "recommendation": "<which look and why, in one sentence>"
}\
"""

QA_SYSTEM_PROMPT = """\
You are MIRA, an elite AI fashion stylist answering a user's follow-up question
about a specific look.

Rules:
- Be conversational, warm, and direct.
- Answer in 2-3 sentences unless the user clearly asks for depth.
- Sound like a trusted stylist speaking to one person, not like a report.
- Ground the answer in the look, the visible garment behavior, the occasion,
  and any provided commentary context.
- Offer practical fashion advice: shoes, layering, fit adjustments, styling,
  event suitability, polish, color balance, and what to change next.
- Never be harsh, body-critical, vague, or overlong.
- Do not restate every available detail unless it directly helps the answer.
- If the question is subjective, give a clear recommendation instead of hedging.
- The answer should feel edited, not exhaustive.

Return ONLY a JSON object:
{
  "answer": "<MIRA's spoken-style answer>",
  "suggested_follow_up": "<optional short follow-up question suggestion or empty string>"
}\
"""

# ---------------------------------------------------------------------------
# Mode instructions
# ---------------------------------------------------------------------------

_MODE_INSTRUCTIONS: dict[CommentaryMode, str] = {
    CommentaryMode.CONCISE_LUXURY: (
        "Deliver 2-3 sentences of elegant, spare commentary for the main text. "
        "Keep the structured fields tight and useful. Do not pad."
    ),
    CommentaryMode.OCCASION_STYLIST: (
        "Focus on event context, appropriateness, and presence. Address how "
        "the look reads upon arrival, the venue feel, time of day, and dress "
        "code nuance. Keep it selective and polished."
    ),
    CommentaryMode.FIT_FOCUSED: (
        "Concentrate on fit, proportion, and size implications. Discuss only "
        "the most meaningful fit and silhouette observations. Avoid turning "
        "the response into a technical report."
    ),
    CommentaryMode.EDITORIAL_BREAKDOWN: (
        "Provide a richer magazine-style analysis in 4-5 sentences. Cover the "
        "most important elements: silhouette, fabric behaviour, colour story, "
        "styling potential, and the strongest refinement opportunity. Be lush "
        "but still disciplined."
    ),
    CommentaryMode.CULTURAL_OCCASION: (
        "Approach with deep cultural styling awareness. Understand the specific "
        "event (sangeet, reception, puja, Eid, etc.) and address traditional "
        "elements alongside modern interpretation. Be culturally fluent, warm, "
        "and restrained."
    ),
    CommentaryMode.COMPARISON: (
        "You are comparing two looks. Offer balanced, specific observations "
        "about each, then a clear recommendation."
    ),
}

# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class StylistService:
    """Generates premium AI fashion commentary via the OpenAI API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_commentary(
        self,
        request: CommentaryRequest,
        user_profile: UserProfile | None = None,
    ) -> StylistCommentary:
        """Generate premium stylist commentary for a look."""
        user_message = self._build_user_message(request, user_profile)

        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=850,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": self._build_user_content(
                        user_message,
                        request.look_image_url,
                    ),
                },
            ],
        )

        parsed = self._parse_response(response.choices[0].message.content or "")

        return StylistCommentary(
            look_id=request.user_profile_id,
            text=parsed.get("text", ""),
            mode=request.mode,
            vibe_tags=self._ensure_list(parsed.get("vibe_tags")),
            occasion_tags=self._ensure_list(parsed.get("occasion_tags")),
            styling_suggestions=self._ensure_list(parsed.get("styling_suggestions")),
            refinement_notes=self._ensure_list(parsed.get("refinement_notes")),
            silhouette_line=parsed.get("silhouette_line"),
            fit_assessment=parsed.get("fit_assessment"),
            proportion=parsed.get("proportion"),
            occasion_read=parsed.get("occasion_read"),
            colour_surface=parsed.get("colour_surface"),
            to_elevate_it=parsed.get("to_elevate_it"),
            tailoring_note=parsed.get("tailoring_note"),
            complete_the_look=self._ensure_list(parsed.get("complete_the_look")),
        )

    async def generate_comparison(
        self,
        look_a: SavedLook,
        look_b: SavedLook,
        user_profile: UserProfile | None = None,
    ) -> str:
        """Compare two looks with editorial commentary."""
        user_parts: list[str] = [
            "Compare the following two looks for the same person.\n",
            f"Look A -- garment image: {look_a.source_garment_url}",
            f"Try-on result: {look_a.try_on_image_url}",
        ]
        if look_a.vibe_tags:
            user_parts.append(f"Vibe: {', '.join(look_a.vibe_tags)}")

        user_parts.append(f"\nLook B -- garment image: {look_b.source_garment_url}")
        user_parts.append(f"Try-on result: {look_b.try_on_image_url}")
        if look_b.vibe_tags:
            user_parts.append(f"Vibe: {', '.join(look_b.vibe_tags)}")

        if user_profile:
            user_parts.append(f"\n{self._profile_context(user_profile)}")

        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=700,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": COMPARISON_SYSTEM_PROMPT},
                {"role": "user", "content": "\n".join(user_parts)},
            ],
        )

        parsed = self._parse_response(response.choices[0].message.content or "")
        return parsed.get("comparison_text", response.choices[0].message.content or "")

    async def answer_question(
        self,
        request: AskStylistRequest,
        user_profile: UserProfile | None = None,
    ) -> AskStylistResponse:
        """Answer a user follow-up about a look in a conversational style."""
        user_message = self._build_question_message(request, user_profile)

        response = await self.client.chat.completions.create(
            model=self.model,
            max_tokens=500,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": QA_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": self._build_user_content(
                        user_message,
                        request.look_image_url,
                    ),
                },
            ],
        )

        parsed = self._parse_response(response.choices[0].message.content or "")
        return AskStylistResponse(
            answer=parsed.get("answer", "").strip() or parsed.get("text", "").strip(),
            suggested_follow_up=(parsed.get("suggested_follow_up") or "").strip() or None,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_mode_instruction(self, mode: CommentaryMode) -> str:
        return _MODE_INSTRUCTIONS.get(
            mode,
            _MODE_INSTRUCTIONS[CommentaryMode.CONCISE_LUXURY],
        )

    def _build_user_message(
        self,
        request: CommentaryRequest,
        user_profile: UserProfile | None,
    ) -> str:
        parts: list[str] = []
        parts.append(f"Commentary mode: {request.mode.value}")
        parts.append(self._build_mode_instruction(request.mode))

        garment_category = (
            request.garment_category.value
            if request.garment_category
            else "unspecified"
        )
        parts.append(f"Garment category: {garment_category}")

        if request.look_image_url.startswith("data:image/"):
            parts.append("Look image: attached below as an inline image.")
        else:
            parts.append(f"Look image URL: {request.look_image_url}")

        if request.occasion:
            parts.append(f"Occasion context: {request.occasion}")

        parts.append(
            "Important: address only the most relevant observations. "
            "Do not force commentary across every dimension."
        )

        if user_profile:
            parts.append(self._profile_context(user_profile))

        return "\n".join(parts)

    def _build_question_message(
        self,
        request: AskStylistRequest,
        user_profile: UserProfile | None,
    ) -> str:
        parts: list[str] = [
            "Answer the user's follow-up question about this look.",
            f"User question: {request.question}",
        ]

        if request.look_image_url.startswith("data:image/"):
            parts.append("Look image: attached below as an inline image.")
        else:
            parts.append(f"Look image URL: {request.look_image_url}")

        if request.occasion:
            parts.append(f"Occasion context: {request.occasion}")
        if request.garment_brand:
            parts.append(f"Garment brand: {request.garment_brand}")
        if request.garment_fit:
            parts.append(f"Garment fit: {request.garment_fit}")

        payload = request.commentary_payload or {}
        if payload:
            parts.append("Existing stylist notes:")
            for label, key in (
                ("Main read", "text"),
                ("Silhouette & line", "silhouette_line"),
                ("Fit assessment", "fit_assessment"),
                ("Proportion", "proportion"),
                ("Occasion read", "occasion_read"),
                ("Colour & surface", "colour_surface"),
                ("To elevate it", "to_elevate_it"),
                ("Tailoring note", "tailoring_note"),
            ):
                value = payload.get(key)
                if value:
                    parts.append(f"- {label}: {value}")

            complete_the_look = payload.get("complete_the_look") or []
            if complete_the_look:
                parts.append(f"- Complete the look: {', '.join(complete_the_look)}")

        if user_profile:
            parts.append(self._profile_context(user_profile))

        parts.append(
            "Keep the answer selective, useful, and concise. "
            "Do not restate everything unless needed."
        )

        return "\n".join(parts)

    @staticmethod
    def _build_user_content(user_message: str, look_image_url: str) -> Any:
        """Attach the look image as multimodal content instead of pasting base64 into text."""
        if not look_image_url:
            return user_message

        return [
            {"type": "text", "text": user_message},
            {"type": "image_url", "image_url": {"url": look_image_url}},
        ]

    @staticmethod
    def _profile_context(profile: UserProfile) -> str:
        lines: list[str] = ["Wearer profile (for personalisation):"]

        if profile.preferred_aesthetic:
            lines.append(f"- Aesthetic: {profile.preferred_aesthetic}")
        if profile.preferred_silhouettes:
            lines.append(
                f"- Preferred silhouettes: {', '.join(profile.preferred_silhouettes)}"
            )
        if profile.favorite_colors:
            lines.append(f"- Favourite colours: {', '.join(profile.favorite_colors)}")
        if profile.disliked_colors:
            lines.append(f"- Colours to avoid: {', '.join(profile.disliked_colors)}")
        if profile.occasions:
            lines.append(f"- Typical occasions: {', '.join(profile.occasions)}")
        if profile.body_highlight_areas:
            lines.append(f"- Likes to highlight: {', '.join(profile.body_highlight_areas)}")
        if profile.body_soft_styling_areas:
            lines.append(
                f"- Prefers relaxed styling around: "
                f"{', '.join(profile.body_soft_styling_areas)}"
            )
        if profile.fit_sensitivities:
            lines.append(f"- Fit sensitivities: {', '.join(profile.fit_sensitivities)}")
        if profile.modesty_preference:
            lines.append(f"- Modesty preference: {profile.modesty_preference}")
        if profile.regional_style_context:
            lines.append(f"- Cultural context: {profile.regional_style_context}")
        if profile.luxury_preference:
            lines.append(f"- Budget tier: {profile.luxury_preference.value}")
        if profile.heel_tolerance:
            lines.append(f"- Heel tolerance: {profile.heel_tolerance}")
        if profile.jewelry_preference:
            lines.append(f"- Jewelry preference: {profile.jewelry_preference}")
        if profile.comfort_vs_statement is not None:
            label = (
                "leans comfort"
                if profile.comfort_vs_statement < 0.35
                else "leans statement"
                if profile.comfort_vs_statement > 0.65
                else "balanced comfort-statement"
            )
            lines.append(f"- Style dial: {label}")

        return "\n".join(lines)

    @staticmethod
    def _ensure_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    @staticmethod
    def _parse_response(raw: str) -> dict[str, Any]:
        raw = raw.strip()

        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]

        raw = raw.strip()

        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
            logger.warning("OpenAI response parsed but was not a JSON object.")
            return {"text": str(parsed)}
        except json.JSONDecodeError:
            logger.warning("Failed to parse OpenAI response as JSON; returning raw text.")
            return {"text": raw}