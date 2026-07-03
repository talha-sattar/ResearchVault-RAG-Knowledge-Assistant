from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import User, UserPreference

DEFAULT_USER_EMAIL_FALLBACK = "you@researchvault.local"


def ensure_default_user(db: Session) -> User:
    """Single-user app: make sure exactly one User row (with preferences) exists."""
    settings = get_settings()
    user = db.query(User).first()
    if user is not None:
        return user

    email = getattr(settings, "owner_email", None) or DEFAULT_USER_EMAIL_FALLBACK
    user = User(email=email, display_name="You")
    db.add(user)
    db.flush()
    db.add(UserPreference(user_id=user.id))
    db.commit()
    db.refresh(user)
    return user
