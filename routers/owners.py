from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import OwnerCreate
from models import Owner
import crud

router = APIRouter(
    prefix="/owners",
    tags=["owners"]
)

@router.post("/")
def create_owner(owner: OwnerCreate, db: Session = Depends(get_db)):
    db_owner = crud.create_owner(db, owner.dict())
    if not db_owner:
        raise HTTPException(status_code=400, detail="Owner creation failed")
    return db_owner

@router.get("/")
def get_all_owners(db: Session = Depends(get_db)):
    return db.query(Owner).all()
@router.delete("/{owner_id}")
def delete_owner(owner_id: int, db: Session = Depends(get_db)):

    try:
        result = crud.delete_record(db, Owner, owner_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))