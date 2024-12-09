from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import ClientCreate
from models import Client
import crud

router = APIRouter(
    prefix="/clients",
    tags=["clients"]
)

@router.post("/")
def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    db_client = crud.create_client(db, client.dict())
    if not db_client:
        raise HTTPException(status_code=400, detail="Client creation failed")
    return db_client

@router.get("/")
def get_all_clients(db: Session = Depends(get_db)):
    return db.query(Client).all()
