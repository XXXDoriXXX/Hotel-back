from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas import LoginRequest, Token
from database import get_db
from crud import authenticate_user
from utils import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=Token)
def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_request.email, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Додаємо owner_id до токена, якщо користувач є власником
    access_token = create_access_token({
        "id": user["id"],
        "email": user["email"],
        "is_owner": user["is_owner"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "phone": user["phone"],
        "owner_id": user.get("owner_id")  # Додаємо owner_id
    })

    return {"access_token": access_token, "token_type": "bearer"}

