from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.db import get_db
from api.dependencies import get_current_user
from api.models.user import User
from api.models.farm import Farm
from api.schemas.farm import FarmCreate, FarmUpdate, FarmResponse

router = APIRouter(prefix="/farms", tags=["Farms"])


@router.post("/", response_model=FarmResponse, status_code=201)
def create_farm(
    req: FarmCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm = Farm(user_id=current_user.id, **req.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/", response_model=list[FarmResponse])
def list_farms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Farm).filter(Farm.user_id == current_user.id).order_by(Farm.created_at.desc()).all()


@router.get("/{farm_id}", response_model=FarmResponse)
def get_farm(
    farm_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm = db.get(Farm, farm_id)
    if not farm or farm.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy ao")
    return farm


@router.patch("/{farm_id}", response_model=FarmResponse)
def update_farm(
    farm_id: str,
    req: FarmUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm = db.get(Farm, farm_id)
    if not farm or farm.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy ao")
    for k, v in req.model_dump(exclude_none=True).items():
        setattr(farm, k, v)
    db.commit()
    db.refresh(farm)
    return farm


@router.delete("/{farm_id}", status_code=204)
def delete_farm(
    farm_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    farm = db.get(Farm, farm_id)
    if not farm or farm.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy ao")
    db.delete(farm)
    db.commit()
