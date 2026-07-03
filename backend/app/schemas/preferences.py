from pydantic import BaseModel


class PreferencesOut(BaseModel):
    favorite_categories: list[str]
    preferred_answer_format: str
    default_top_k: int | None


class PreferencesUpdate(BaseModel):
    favorite_categories: list[str] | None = None
    preferred_answer_format: str | None = None
    default_top_k: int | None = None
