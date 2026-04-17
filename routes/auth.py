from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional

from core.database import get_db, SessionLocal
from core.auth import hash_password, verify_password, create_access_token
from models.schemas import UserCreate, Token
from models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


def create_default_user():
    """Create default admin user if no users exist"""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if not existing:
            user = User(
                username="admin",
                hashed_password=hash_password("admin")
            )
            db.add(user)
            db.commit()
            print("✅ Default user created: admin / admin")
    except Exception as e:
        print(f"Error creating default user: {e}")
    finally:
        db.close()


@router.on_event("startup")
async def startup_event():
    create_default_user()


@router.post("/register", status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User registered", "username": user.username}


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login using form data (username/password) - compatible with frontend"""
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({"sub": user.username, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}