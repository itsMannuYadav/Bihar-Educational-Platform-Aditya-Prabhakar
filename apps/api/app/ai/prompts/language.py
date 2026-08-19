from app.db.models.enums import AppLanguage

# Bilingual generation is a first-class parameter, not a translation
# post-process (docs/01-architecture.md §5) — every prompt gets a register
# instruction rather than "write in English then translate."
LANGUAGE_INSTRUCTIONS: dict[AppLanguage, str] = {
    AppLanguage.en: (
        "Write entirely in clear, simple English suitable for a government-school classroom."
    ),
    AppLanguage.hi: "पूरी सामग्री शुद्ध, सरल हिंदी में लिखें, जैसा एक सरकारी स्कूल का शिक्षक बोलता है।",
    AppLanguage.hinglish: (
        "Write in Hinglish — natural code-mixed Hindi-English in Roman script, the way "
        "Bihar teachers actually speak in class. This is not a translation of English; "
        "write directly in this register."
    ),
}
