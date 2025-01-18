import os
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from dependencies import is_hotel_owner, get_current_user
from schemas import RoomCreate
from models import Room, RoomImage
import crud

router = APIRouter(
    prefix="/rooms",
    tags=["rooms"]
)
UPLOAD_DIRECTORY = "uploaded_images/rooms"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
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
@router.post("/{room_id}/images/upload/")
async def upload_room_image(
    room_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    is_hotel_owner(current_user, room.hotel_id, db)

    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Invalid file format. Only jpg, jpeg, and png are allowed.")

    filename = f"{uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    image_url = f"/{UPLOAD_DIRECTORY}/{filename}"

    try:
        room_image = crud.add_room_image(db, room_id=room_id, image_url=image_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving image record: {str(e)}")

    return {"id": room_image.id, "image_url": image_url}

@router.delete("/images/{image_id}")
def delete_room_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    image = db.query(RoomImage).filter(RoomImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    room = db.query(Room).filter(Room.id == image.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    is_hotel_owner(current_user, room.hotel_id, db)

    file_path = image.image_url.lstrip("/")
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(image)
    db.commit()
    return {"detail": "Image deleted successfully"}
@router.get("/{room_id}/images/")
def get_room_images(room_id: int, db: Session = Depends(get_db)):
    images = db.query(RoomImage).filter(RoomImage.room_id == room_id).all()
    return images
