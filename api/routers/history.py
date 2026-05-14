from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.db import get_db
from api.dependencies import get_current_user
from api.models.user import User
from api.models.history import DiagnoseHistory
from api.models.schedule_history import ScheduleHistory
from api.schemas.history import HistoryItem, HistoryList
from api.schemas.schedule_history import ScheduleHistoryItem, ScheduleHistoryList

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
    h = db.get(DiagnoseHistory, history_id)
    if not h or h.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy")
    return h


@router.delete("/{history_id}", status_code=204)
def delete_history(
    history_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    h = db.get(DiagnoseHistory, history_id)
    if not h or h.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy")
    db.delete(h)
    db.commit()


# ── Schedule history ──────────────────────────────────────────────────────────

@router.get("/schedules/", response_model=ScheduleHistoryList)
def list_schedule_history(
    limit:  int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(ScheduleHistory).filter(ScheduleHistory.user_id == current_user.id)
    total = q.count()
    items = q.order_by(ScheduleHistory.created_at.desc()).offset(offset).limit(limit).all()
    return ScheduleHistoryList(total=total, items=items)


@router.delete("/schedules/{schedule_id}", status_code=204)
def delete_schedule_history(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    h = db.get(ScheduleHistory, schedule_id)
    if not h or h.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy")
    db.delete(h)
    db.commit()
