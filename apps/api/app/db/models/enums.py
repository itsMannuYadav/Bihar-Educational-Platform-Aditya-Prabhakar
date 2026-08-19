import enum


class UserRole(enum.StrEnum):
    teacher = "teacher"
    school_admin = "school_admin"
    super_admin = "super_admin"


class AppLanguage(enum.StrEnum):
    en = "en"
    hi = "hi"
    hinglish = "hinglish"
