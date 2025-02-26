from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models import Person
from schemas import LoginRequest, Token, PersonCreate, PersonBase
from database import get_db
from crud import authenticate_user, create_person, create_owner, create_client
from utils import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=PersonBase, status_code=status.HTTP_201_CREATED)
def register(user: PersonCreate, db: Session = Depends(get_db)):
    existing_user = db.query(Person).filter(
        (Person.email == user.email) | (Person.phone == user.phone)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email or phone already exists."
        )

    if user.is_owner:
        new_owner = create_owner(db, user.dict())
        return PersonBase(**new_owner.person.__dict__)  # Перетворюємо у відповідну модель
    else:
        new_client = create_client(db, user.dict())
        return PersonBase(**new_client.person.__dict__)  # Аналогічно

@router.post("/login", response_model=Token)
def login(login_request: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_request.email, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({
        "id": user["id"],
        "email": user["email"],
        "is_owner": user["is_owner"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "phone": user["phone"],
        "birth_date": user["birth_date"],
        "owner_id": user.get("owner_id")
    })

    return {"access_token": access_token, "token_type": "bearer"}

