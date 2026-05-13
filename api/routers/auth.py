from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from api.db import get_db
from api.auth import hash_password, verify_password, create_token
from api.dependencies import get_current_user
from api.models.user import User
from api.schemas.auth import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        phone=req.phone,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Email đã được đăng ký")
    return TokenResponse(
        access_token=create_token(user.id),
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email hoặc mật khẩu không đúng")
    return TokenResponse(
        access_token=create_token(user.id),
        user_id=user.id,
        full_name=user.full_name,
        email=user.email,
    )


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "user_id":   current_user.id,
        "email":     current_user.email,
        "full_name": current_user.full_name,
        "phone":     current_user.phone,
    }
