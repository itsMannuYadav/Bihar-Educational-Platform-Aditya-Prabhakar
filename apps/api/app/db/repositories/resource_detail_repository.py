import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.enums import Difficulty, QuestionType
from app.db.models.resource_detail import MindMap, Presentation, Question, Worksheet


async def create_questions(
    db: AsyncSession,
    *,
    resource_id: uuid.UUID,
    questions: list[dict],
) -> list[Question]:
    rows = [
        Question(
            resource_id=resource_id,
            type=QuestionType(q["type"]),
            difficulty=Difficulty(q["difficulty"]),
            question_text=q["question_text"],
            options=q.get("options"),
            answer=q.get("answer"),
            explanation=q.get("explanation"),
            is_previous_year=False,
        )
        for q in questions
    ]
    db.add_all(rows)
    await db.flush()
    return rows


async def create_worksheet(
    db: AsyncSession, *, resource_id: uuid.UUID, sections: list[dict]
) -> Worksheet:
    worksheet = Worksheet(resource_id=resource_id, sections=sections)
    db.add(worksheet)
    await db.flush()
    return worksheet


async def create_mind_map(
    db: AsyncSession, *, resource_id: uuid.UUID, structure: dict
) -> MindMap:
    mind_map = MindMap(resource_id=resource_id, structure=structure)
    db.add(mind_map)
    await db.flush()
    return mind_map


async def create_presentation(
    db: AsyncSession, *, resource_id: uuid.UUID, slide_count: int, slides: dict
) -> Presentation:
    presentation = Presentation(resource_id=resource_id, slide_count=slide_count, slides=slides)
    db.add(presentation)
    await db.flush()
    return presentation
