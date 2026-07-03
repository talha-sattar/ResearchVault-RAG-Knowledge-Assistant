from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.memory import preferences as preferences_module
from app.schemas.preferences import PreferencesOut, PreferencesUpdate

router = APIRouter(prefix="/preferences", tags=["preferences"])


def _to_schema(pref) -> PreferencesOut:
    return PreferencesOut(
        favorite_categories=pref.favorite_categories,
        preferred_answer_format=pref.preferred_answer_format.value,
        default_top_k=pref.default_top_k,
    )


@router.get("", response_model=PreferencesOut)
def get_preferences(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> PreferencesOut:
    return _to_schema(preferences_module.get_preferences(db, user))


@router.put("", response_model=PreferencesOut)
def update_preferences(
    body: PreferencesUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PreferencesOut:
    pref = preferences_module.update_preferences(
        db,
        user,
        favorite_categories=body.favorite_categories,
        preferred_answer_format=body.preferred_answer_format,
        default_top_k=body.default_top_k,
    )
    return _to_schema(pref)
