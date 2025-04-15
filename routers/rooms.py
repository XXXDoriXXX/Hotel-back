import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid, boto3


from database import get_db
from dependencies import get_current_owner
from models import Room, Hotel, RoomImg, AmenityRoom
from schemas import RoomBase, RoomCreate, RoomDetails, RoomImgBase
from schemas.amenities import AmenityRoomBase
from schemas.room import RoomCreateRequest

router = APIRouter(prefix="/rooms", tags=["rooms"])
S3_BUCKET = os.getenv('S3_BUCKET')
S3_REGION = os.getenv('S3_REGION')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
s3_client = boto3.client("s3")
ALLOWED_IMAGE_TYPES = ["jpg", "jpeg", "png", "webp"]

# ---------------- CREATE ROOM ----------------
@router.post("/", response_model=RoomDetails, status_code=201)
def create_room(
    room_data: RoomCreateRequest,
    db: Session = Depends(get_db),
    current_owner=Depends(get_current_owner)
):
    existing_room = db.query(Room).filter(
        Room.room_number == room_data.room_number,
        Room.hotel_id == room_data.hotel_id
    ).first()
    if existing_room:
        raise HTTPException(status_code=400, detail="Room number already exists in this hotel")

    hotel = db.query(Hotel).filter(Hotel.id == room_data.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(403, "Not authorized to add room to this hotel")

    db_room = Room(**room_data.dict(exclude={"amenity_ids"}))
    db.add(db_room)
    db.commit()
    db.refresh(db_room)

    if room_data.amenity_ids:
        for amenity_id in room_data.amenity_ids:
            db.add(AmenityRoom(room_id=db_room.id, amenity_id=amenity_id))

    db.commit()
    db.refresh(db_room)
    return db_room
# ---------------- GET ALL ROOMS ----------------
@router.get("/", response_model=List[RoomDetails])
def get_rooms(
    hotel_id: int = None,
    db: Session = Depends(get_db)
):
    query = db.query(Room)
    if hotel_id:
        query = query.filter(Room.hotel_id == hotel_id)
    return query.all()

# ---------------- GET ROOM BY ID ----------------
@router.get("/{room_id}", response_model=RoomDetails)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")
    return room

# ---------------- DELETE ROOM ----------------
@router.delete("/{room_id}")
def delete_room(room_id: int, db: Session = Depends(get_db), current_owner = Depends(get_current_owner)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")

    hotel = db.query(Hotel).filter(Hotel.id == room.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(403, "Not authorized")

    db.delete(room)
    db.commit()
    return {"message": "Room deleted successfully"}
# ---------------- UPDATE ROOM ----------------
@router.put("/{room_id}", response_model=RoomDetails)
def update_room(
    room_id: int,
    room_data: RoomCreateRequest,
    db: Session = Depends(get_db),
    current_owner=Depends(get_current_owner)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")

    hotel = db.query(Hotel).filter(Hotel.id == room.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(403, "Not authorized to update this room")

    for key, value in room_data.dict(exclude={"amenity_ids"}).items():
        setattr(room, key, value)

    db.query(AmenityRoom).filter(AmenityRoom.room_id == room_id).delete()
    if room_data.amenity_ids:
        for amenity_id in room_data.amenity_ids:
            db.add(AmenityRoom(room_id=room_id, amenity_id=amenity_id))

    db.commit()
    db.refresh(room)
    return room
# ---------------- ADD ROOM IMAGES ----------------
@router.post("/{room_id}/images", response_model=RoomImgBase)
async def upload_room_image(
    room_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_owner = Depends(get_current_owner)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")

    hotel = db.query(Hotel).filter(Hotel.id == room.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(403, "Not authorized")

    ext = file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(400, "Invalid image format")

    filename = f"{uuid.uuid4()}.{ext}"
    s3_key = f"rooms/{room_id}/{filename}"

    try:
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": file.content_type}
        )

        url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        image = RoomImg(room_id=room_id, image_url=url)
        db.add(image)
        db.commit()
        db.refresh(image)
        return image
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")


# ---------------- GET ROOM IMAGES ----------------
@router.get("/{room_id}/images", response_model=List[RoomImgBase])
def get_room_images(room_id: int, db: Session = Depends(get_db)):
    return db.query(RoomImg).filter(RoomImg.room_id == room_id).all()


# ---------------- DELETE IMAGE BY ID ----------------
@router.delete("/images/{image_id}")
def delete_room_image(image_id: int, db: Session = Depends(get_db), current_owner = Depends(get_current_owner)):
    image = db.query(RoomImg).filter(RoomImg.id == image_id).first()
    if not image:
        raise HTTPException(404, "Image not found")

    room = db.query(Room).filter(Room.id == image.room_id).first()
    hotel = db.query(Hotel).filter(Hotel.id == room.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(403, "Not authorized")

    s3_key = image.image_url.split(f"{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/")[-1]
    s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)

    db.delete(image)
    db.commit()
    return {"message": "Image deleted"}

# ---------------- ADD AMENITIES ----------------
@router.post("/{room_id}/amenities")
def add_room_amenities(
    room_id: int,
    amenity_ids: List[int],
    db: Session = Depends(get_db),
    current_owner = Depends(get_current_owner)
):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")

    hotel = db.query(Hotel).filter(Hotel.id == room.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(403, "Not authorized")

    db.query(AmenityRoom).filter(AmenityRoom.room_id == room_id).delete()

    for amenity_id in amenity_ids:
        db.add(AmenityRoom(room_id=room_id, amenity_id=amenity_id))

    db.commit()
    return {"message": "Room amenities updated"}

# ---------------- GET AMENITIES  ----------------
@router.get("/{room_id}/amenities", response_model=List[AmenityRoomBase])
def get_room_amenities(room_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(404, "Room not found")

    return db.query(AmenityRoom).filter(AmenityRoom.room_id == room_id).all()
