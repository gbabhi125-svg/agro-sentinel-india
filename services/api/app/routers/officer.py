"""
Read-only aggregated view for an agriculture extension officer (plan item
#13) — counts and top causes across all farmers using the app, never a
single farmer's identity (none is collected in the schema to begin with).
"""
from fastapi import APIRouter

from ..storage import db

router = APIRouter(prefix="/api/officer", tags=["officer"])


@router.get("/summary")
def summary(days: int = 30):
    return db.officer_summary(days)
