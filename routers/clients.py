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
@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):

    try:
        deleted_client = crud.delete_record(db, Client, client_id)
        return deleted_client
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
