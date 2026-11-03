from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=schemas.TokenResponse, status_code=201)
def signup(body: schemas.SignupRequest, db: Session = Depends(get_db)):
    email = body.email.lower()
    if db.query(models.User).filter(models.User.email == email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists.")
    user = models.User(
        name=body.name.strip(),
        email=email,
        hashed_password=security.hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return schemas.TokenResponse(
        access_token=security.create_access_token(user.id),
        user=schemas.UserOut.model_validate(user),
    )


@router.post("/login", response_model=schemas.TokenResponse)
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email.lower()).first()
    if not user or not security.verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
    return schemas.TokenResponse(
        access_token=security.create_access_token(user.id),
        user=schemas.UserOut.model_validate(user),
    )


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(security.get_current_user)):
    return current_user
