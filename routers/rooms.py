import os
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from starlette import status

import schemas
from crud import room_crud
from database import get_db
from dependencies import is_hotel_owner, get_current_user, get_current_owner
from routers.hotels import DescriptionUpdate
from schemas import RoomCreate, RoomDetails
from models import Room, RoomImage, Hotel
import crud.room_crud

router = APIRouter(
    prefix="/rooms",
    tags=["rooms"]
)
UPLOAD_DIRECTORY = "uploaded_images/rooms"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png", "webp"]

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_room(
    room: RoomCreate,
    db: Session = Depends(get_db),
    current_owner: dict = Depends(get_current_owner)
):
    hotel = db.query(Hotel).filter(Hotel.id == room.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create rooms in this hotel"
        )

    db_room = room_crud.create_room(db, room.dict())
    if not db_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Room creation failed"
        )
    return db_room
@router.get("/search", response_model=List[RoomDetails])
def search_rooms(
    hotel_id: int,
    room_number: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    places: Optional[int] = None,
    room_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Room).filter(Room.hotel_id == hotel_id)

    if room_number:
        query = query.filter(Room.room_number.ilike(f"%{room_number}%"))
    if min_price:
        query = query.filter(Room.price_per_night >= min_price)
    if max_price:
        query = query.filter(Room.price_per_night <= max_price)
    if places:
        query = query.filter(Room.places == places)
    if room_type:
        query = query.filter(Room.room_type.ilike(f"%{room_type}%"))

    rooms = query.all()
    if not rooms:
        raise HTTPException(status_code=404, detail="No rooms found")
    return rooms

@router.get("/")
def get_all_rooms(db: Session = Depends(get_db)):
    return db.query(Room).all()


@router.get("/{room_id}", response_model=RoomDetails)
def get_room(
    room_id: int,
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    return room


@router.delete("/{room_id}")
def delete_room(
        room_id: int,
        db: Session = Depends(get_db),
        current_owner: dict = Depends(get_current_owner)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    hotel = db.query(Hotel).filter(Hotel.id == room.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this room"
        )

    try:
        deleted = room_crud.delete_room(db, room_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete room"
            )
        return {"message": "Room deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{room_id}/images/upload/", status_code=status.HTTP_201_CREATED)
async def upload_room_image(
        room_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_owner: dict = Depends(get_current_owner)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    hotel = db.query(Hotel).filter(Hotel.id == room.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload images for this room"
        )

    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file format. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    filename = f"{uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving file: {str(e)}"
        )

    image_url = f"/{UPLOAD_DIRECTORY}/{filename}"

    try:
        room_image = room_crud.add_room_image(db, room_id=room_id, image_url=image_url)
        return {
            "id": room_image.id,
            "image_url": image_url,
            "message": "Image uploaded successfully"
        }
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving image record: {str(e)}"
        )


@router.delete("/images/{image_id}")
def delete_room_image(
        image_id: int,
        db: Session = Depends(get_db),
        current_owner: dict = Depends(get_current_owner)
):
    image = db.query(RoomImage).filter(RoomImage.id == image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )

    room = db.query(Room).filter(Room.id == image.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    # Verify the owner owns the hotel
    hotel = db.query(Hotel).filter(Hotel.id == room.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this image"
        )

    file_path = image.image_url.lstrip("/")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting file: {str(e)}"
            )

    db.delete(image)
    db.commit()
    return {"message": "Image deleted successfully"}


@router.get("/{room_id}/images/", response_model=List[schemas.RoomImageBase])
def get_room_images(
    room_id: int,
    db: Session = Depends(get_db)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    images = db.query(RoomImage).filter(RoomImage.room_id == room_id).all()
    return images


@router.put("/{room_id}/description")
def update_room_description(
        room_id: int,
        body: DescriptionUpdate,
        db: Session = Depends(get_db),
        current_owner: dict = Depends(get_current_owner)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )

    hotel = db.query(Hotel).filter(Hotel.id == room.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this room"
        )

    if len(body.description) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description must not exceed 500 characters"
        )

    room.description = body.description
    db.commit()
    db.refresh(room)
    return {
        "message": "Room description updated successfully",
        "description": room.description
    }