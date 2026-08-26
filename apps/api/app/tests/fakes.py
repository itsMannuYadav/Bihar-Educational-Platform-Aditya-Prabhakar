from pydantic import BaseModel

from app.ai.prompts.audio import AudioScripts
from app.ai.prompts.lesson_plan import LessonPlanContent
from app.ai.prompts.mind_map import MindMapBranch, MindMapLeaf, MindMapOutline
from app.ai.prompts.presentation import PresentationOutline, Slide
from app.ai.prompts.questions import QuestionItem, QuestionOption, QuestionSetContent
from app.ai.prompts.teaching_script import ScriptSection, TeachingScriptContent
from app.ai.prompts.worksheet import (
    FillBlankItem,
    MatchItem,
    TrueFalseItem,
    WorksheetContent,
    WorksheetSection,
)
from app.db.models.enums import AppLanguage


def _lesson_plan() -> LessonPlanContent:
    return LessonPlanContent(
        objectives=["Understand the core idea of the chapter"],
        introduction="A short hook to open the class.",
        core_concepts=["Concept one", "Concept two"],
        classroom_discussion=["Why does this happen?", "Can you think of an example?"],
        assessment=["Short oral quiz on the core concepts"],
        homework="Read the chapter summary and answer question 1.",
    )


def _teaching_script() -> TeachingScriptContent:
    return TeachingScriptContent(
        opening="Bachcho, aaj hum ek nayi cheez seekhenge.",
        sections=[
            ScriptSection(
                heading="Concept one",
                script="Dekho, jab paudhe dhoop mein rehte hain…",
                discussion_prompt="Aapne kahan dekha hai aisa hote hue?",
            )
        ],
        closing="Toh aaj humne kya seekha?",
    )


def _questions() -> QuestionSetContent:
    return QuestionSetContent(
        questions=[
            QuestionItem(
                type="mcq",
                difficulty="easy",
                question_text="Which part of the plant makes food?",
                options=[
                    QuestionOption(label="A", text="Leaf", is_correct=True),
                    QuestionOption(label="B", text="Root", is_correct=False),
                    QuestionOption(label="C", text="Stem", is_correct=False),
                    QuestionOption(label="D", text="Flower", is_correct=False),
                ],
                answer="Leaf",
                explanation="Leaves contain chlorophyll.",
            ),
            QuestionItem(
                type="short_answer",
                difficulty="moderate",
                question_text="Define photosynthesis.",
                answer="The process by which plants make food using sunlight.",
            ),
        ]
    )


def _worksheet() -> WorksheetContent:
    return WorksheetContent(
        sections=[
            WorksheetSection(
                type="fill_blank",
                fill_blank_items=[
                    FillBlankItem(text="Plants make food in the ____.", answer="leaf")
                ],
            ),
            WorksheetSection(
                type="true_false",
                true_false_items=[TrueFalseItem(statement="Roots make food.", is_true=False)],
            ),
            WorksheetSection(
                type="match",
                match_items=[MatchItem(left="Chlorophyll", right="Green pigment")],
            ),
        ]
    )


def _mind_map() -> MindMapOutline:
    return MindMapOutline(
        id="root",
        label="Nutrition in Plants",
        sub_topics=[
            MindMapBranch(
                id="auto",
                label="Autotrophic",
                key_points=[MindMapLeaf(id="photo", label="Photosynthesis")],
            ),
            MindMapBranch(id="hetero", label="Heterotrophic", key_points=[]),
        ],
    )


def _audio() -> AudioScripts:
    return AudioScripts(
        one_minute="Bachcho, aaj hum seekhenge photosynthesis ke baare mein. Ek minute mein.",
        three_minutes="Namaste! Aaj teen minute mein hum samjhenge ki paudhe apna khana kaise banate hain.",  # noqa: E501
        five_minutes=(
            "Hello students! Aaj ka humara topic bahut interesting hai — photosynthesis. "
            "Chalo shuru karte hain... (full five minute narration)"
        ),
    )


def _presentation() -> PresentationOutline:
    # 15 slides so trim_slides() has something real to derive the 5/10 decks from.
    return PresentationOutline(
        slides=[
            Slide(
                layout="title" if i == 0 else "bullets",
                title=f"Slide {i + 1}",
                body=[f"Point {i + 1}"],
                speaker_notes=f"Say this on slide {i + 1}.",
            )
            for i in range(15)
        ]
    )


CANNED_RESPONSES = {
    LessonPlanContent: _lesson_plan,
    TeachingScriptContent: _teaching_script,
    QuestionSetContent: _questions,
    WorksheetContent: _worksheet,
    MindMapOutline: _mind_map,
    PresentationOutline: _presentation,
    AudioScripts: _audio,
}


class FakeTTSProvider:
    """Test double for TTSProvider — returns a minimal valid MP3 header."""

    def __init__(self) -> None:
        self.call_count = 0

    async def synthesize(self, text: str, *, voice: str | None = None) -> bytes:
        self.call_count += 1
        # A real MP3 starts with 0xFF 0xFB; browsers won't complain about a
        # short fake but it keeps the content-type honest in tests.
        return b"\xff\xfb\x90\x00" + b"\x00" * 128


class FakeLLMProvider:
    """Test double for LLMProvider — no network calls, tracks how many times
    it was invoked so cache-hit tests can assert the LLM wasn't called twice.
    """

    def __init__(self) -> None:
        self.call_count = 0

    async def generate(
        self, prompt: str, *, language: AppLanguage, response_schema: type[BaseModel]
    ) -> BaseModel:
        self.call_count += 1
        build = CANNED_RESPONSES.get(response_schema)
        if build is None:
            raise NotImplementedError(
                f"FakeLLMProvider has no canned response for {response_schema.__name__}"
            )
        return build()
