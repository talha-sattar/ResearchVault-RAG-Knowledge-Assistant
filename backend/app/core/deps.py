from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import User
from app.services.bootstrap import ensure_default_user


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Single-user app: no auth, always resolves to the one bootstrapped User row."""
    return ensure_default_user(db)
