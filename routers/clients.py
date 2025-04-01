from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas import ClientCreate
from models import Client

router = APIRouter(
    prefix="/clients",
    tags=["clients"]
)

@router.get("/")
def get_all_clients(db: Session = Depends(get_db)):
    return db.query(Client).all()
