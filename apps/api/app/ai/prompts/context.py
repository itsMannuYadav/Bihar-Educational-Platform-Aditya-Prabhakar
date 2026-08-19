def lesson_plan_summary(lesson_plan_content: dict) -> str:
    """Grounds every other resource in the same lesson plan (docs/01-architecture.md
    §3: lesson plan is "the shared source of truth every other resource
    references") instead of each node re-deriving objectives/core concepts
    independently.
    """
    objectives = lesson_plan_content.get("objectives") or []
    core_concepts = lesson_plan_content.get("core_concepts") or []
    lines = ["This must align with the lesson plan already prepared for this class:"]
    if objectives:
        lines.append("Learning objectives: " + "; ".join(objectives))
    if core_concepts:
        lines.append("Core concepts: " + "; ".join(core_concepts))
    return "\n".join(lines)
