from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import EmailStr
from sqlalchemy.orm import Session

from crud import person_crud
from database import get_db
from dependencies import oauth2_scheme
from schemas import ClientCreate, OwnerCreate
from schemas.auth import Token

from utils import create_access_token, verify_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register/client", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_client(user: ClientCreate, db: Session = Depends(get_db)):
    existing = db.query(person_crud.Client).filter(
        (person_crud.Client.email == user.email) | (person_crud.Client.phone == user.phone)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Client already exists")

    new_client = person_crud.create_client(db, user.dict())

    token_data = {
        "id": new_client.id,
        "first_name": new_client.first_name,
        "last_name": new_client.last_name,
        "email": new_client.email,
        "phone": new_client.phone,
        "is_owner": False,
        "birth_date": new_client.birth_date
    }
    token = create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/register/owner", response_model=Token, status_code=status.HTTP_201_CREATED)
def register_owner(user: OwnerCreate, db: Session = Depends(get_db)):
    existing = db.query(person_crud.Owner).filter(
        (person_crud.Owner.email == user.email) | (person_crud.Owner.phone == user.phone)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Owner already exists")

    new_owner = person_crud.create_owner(db, user.dict())

    token_data = {
        "id": new_owner.id,
        "first_name": new_owner.first_name,
        "last_name": new_owner.last_name,
        "email": new_owner.email,
        "phone": new_owner.phone,
        "is_owner": True,
        "birth_date": None,
        "owner_id": new_owner.id
    }
    token = create_access_token(token_data)
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
def login(
    email: Annotated[EmailStr, Body(embed=True)],
    password: Annotated[str, Body(embed=True)],
    db: Session = Depends(get_db)
):
    user = person_crud.authenticate_user(db, email, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"user": payload}