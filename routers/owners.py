
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Owner

router = APIRouter(
    prefix="/owners",
    tags=["owners"]
)
@router.get("/")
def get_all_owners(db: Session = Depends(get_db)):
    return db.query(Owner).all()
