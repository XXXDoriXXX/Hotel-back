from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import RoomCreate
from models import Room
import crud

router = APIRouter(
    prefix="/rooms",
    tags=["rooms"]
)

@router.post("/")
def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    db_room = crud.create_room(db, room.dict())
    if not db_room:
        raise HTTPException(status_code=400, detail="Room creation failed")
    return db_room

@router.get("/")
def get_all_rooms(db: Session = Depends(get_db)):
    return db.query(Room).all()

@router.get("/{room_id}")
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room
@router.delete("/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db)):

    try:
        deleted_room = crud.delete_record(db,Room, room_id)
        return deleted_room
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
