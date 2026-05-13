from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.db import get_db
from api.dependencies import get_current_user
from api.models.user import User
from api.models.history import DiagnoseHistory
from api.schemas.history import HistoryItem, HistoryList

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/", response_model=HistoryList)
def list_history(
    farm_id: str | None = Query(None),
    limit:   int        = Query(20, ge=1, le=100),
    offset:  int        = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(DiagnoseHistory).filter(DiagnoseHistory.user_id == current_user.id)
    if farm_id:
        q = q.filter(DiagnoseHistory.farm_id == farm_id)
    total = q.count()
    items = q.order_by(DiagnoseHistory.created_at.desc()).offset(offset).limit(limit).all()
    return HistoryList(total=total, items=items)


@router.get("/{history_id}", response_model=HistoryItem)
def get_history(
    history_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException, status
    h = db.get(DiagnoseHistory, history_id)
    if not h or h.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy")
    return h
