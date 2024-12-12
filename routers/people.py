from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Person
from typing import List
from schemas import PersonBase

router = APIRouter(
    prefix="/people",
    tags=["people"]
)

@router.get("/", response_model=List[PersonBase])
def get_all_people(db: Session = Depends(get_db)):
    return db.query(Person).all()
