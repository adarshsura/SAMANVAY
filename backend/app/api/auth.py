from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.database.models import User, Responder
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.core.security import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Please verify your username and password."
        )

    responder_id = None
    name = user.username
    if user.role == "RESPONDER":
        responder = db.query(Responder).filter(Responder.user_id == user.id).first()
        if responder:
            responder_id = responder.id
            name = responder.name

    token = create_access_token({
        "sub": user.id,
        "username": user.username,
        "role": user.role,
        "responder_id": responder_id
    })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        username=user.username,
        role=user.role,
        responder_id=responder_id,
        name=name
    )

@router.get("/me", response_model=UserResponse)
def get_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active
    )
