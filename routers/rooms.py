import os
import uuid
from typing import List, Optional
from uuid import uuid4

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from starlette import status

import schemas
from crud import room_crud
from database import get_db
from dependencies import is_hotel_owner, get_current_user, get_current_owner
from routers.hotels import DescriptionUpdate, S3_BUCKET, S3_REGION, s3_client
from models import Room, Hotel, Media
import crud.room_crud
from schemas import RoomCreate, RoomDetails

router = APIRouter(
    prefix="/rooms",
    tags=["rooms"]
)

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


async def upload_room_image(
        room_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_owner: dict = Depends(get_current_owner)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    hotel = db.query(Hotel).filter(Hotel.id == room.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    filename = f"{uuid.uuid4()}.{file_extension}"
    s3_key = f"rooms/{room_id}/{filename}"

    try:
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={
                'ContentType': file.content_type,
                'ACL': 'public-read'
            }
        )

        image_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        room_image = room_crud.add_room_media(db, room_id=room_id, image_url=image_url)

        return {
            "id": room_image.id,
            "image_url": image_url,
            "message": "Image uploaded successfully"
        }
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file to S3: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving image record: {str(e)}"
        )


@router.delete("/images/{image_id}")
def delete_room_image(
        image_id: int,
        db: Session = Depends(get_db),
        current_owner: dict = Depends(get_current_owner)
):
    image = db.query(Media).filter(Media.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    room = db.query(Room).filter(Room.id == image.entity_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    hotel = db.query(Hotel).filter(Hotel.id == room.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        s3_key = image.image_url.split(f"{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/")[-1]
        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)

        db.delete(image)
        db.commit()
        return {"message": "Image deleted successfully"}
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting file from S3: {str(e)}"
        )


from models import Media, EntityType
from typing import List
import schemas


@router.get("/{room_id}/images/", response_model=List[schemas.MediaBase])
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

    images = db.query(Media).filter(
        Media.entity_type == EntityType.ROOM,
        Media.entity_id == room_id
    ).all()

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