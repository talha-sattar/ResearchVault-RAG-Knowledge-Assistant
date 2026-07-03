from sqlalchemy.orm import Session

from app.db.enums import AnswerFormat
from app.db.models import User, UserPreference


def get_preferences(db: Session, user: User) -> UserPreference:
    pref = db.query(UserPreference).filter(UserPreference.user_id == user.id).one_or_none()
    if pref is None:
        pref = UserPreference(user_id=user.id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


def update_preferences(
    db: Session,
    user: User,
    favorite_categories: list[str] | None = None,
    preferred_answer_format: str | None = None,
    default_top_k: int | None = None,
) -> UserPreference:
    pref = get_preferences(db, user)
    if favorite_categories is not None:
        pref.favorite_categories = favorite_categories
    if preferred_answer_format is not None:
        pref.preferred_answer_format = AnswerFormat(preferred_answer_format)
    if default_top_k is not None:
        pref.default_top_k = default_top_k
    db.commit()
    db.refresh(pref)
    return pref
