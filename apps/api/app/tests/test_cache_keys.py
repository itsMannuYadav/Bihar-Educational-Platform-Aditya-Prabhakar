import uuid

from app.cache.keys import compute_cache_key
from app.db.models.enums import AppLanguage, DurationOption, ResourceType, TeachingMode

CLASS_ID = uuid.uuid4()
SUBJECT_ID = uuid.uuid4()
CHAPTER_ID = uuid.uuid4()


def _key(**overrides: object) -> str:
    defaults = {
        "class_id": CLASS_ID,
        "subject_id": SUBJECT_ID,
        "chapter_id": CHAPTER_ID,
        "language": AppLanguage.hi,
        "duration": DurationOption.forty,
        "teaching_mode": TeachingMode.concept,
        "resource_type": ResourceType.lesson_plan,
        "params": {},
    }
    defaults.update(overrides)
    return compute_cache_key(**defaults)  # type: ignore[arg-type]


def test_same_inputs_produce_same_key() -> None:
    assert _key() == _key()


def test_different_language_produces_different_key() -> None:
    assert _key(language=AppLanguage.hi) != _key(language=AppLanguage.en)


def test_different_resource_type_produces_different_key() -> None:
    assert _key(resource_type=ResourceType.lesson_plan) != _key(
        resource_type=ResourceType.questions
    )


def test_param_key_order_does_not_affect_cache_key() -> None:
    key_a = _key(params={"difficulty": "easy", "count": 5})
    key_b = _key(params={"count": 5, "difficulty": "easy"})
    assert key_a == key_b


def test_different_param_values_produce_different_key() -> None:
    assert _key(params={"difficulty": "easy"}) != _key(params={"difficulty": "advanced"})
