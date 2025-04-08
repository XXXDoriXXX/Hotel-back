from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Client

router = APIRouter(
    prefix="/clients",
    tags=["clients"]
)

@router.get("/")
def get_all_clients(db: Session = Depends(get_db)):
    return db.query(Client).all()
