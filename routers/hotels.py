import os
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user, is_hotel_owner
from schemas import HotelCreate
from models import Hotel, HotelImage
import crud

router = APIRouter(
    prefix="/hotels",
    tags=["hotels"]
)
UPLOAD_DIRECTORY = "uploaded_images/hotels"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
@router.post("/")
def create_hotel(hotel: HotelCreate, db: Session = Depends(get_db)):
    db_hotel = crud.create_hotel(db, hotel.dict())
    if not db_hotel:
        raise HTTPException(status_code=400, detail="Hotel creation failed")
    return db_hotel
@router.get("/all_details")
def get_all_hotels_with_details(db: Session = Depends(get_db)):
    hotels = db.query(Hotel).all()
    result = []
    for hotel in hotels:
        # Отримання зображень готелю
        hotel_images = [
            {"id": image.id, "image_url": image.image_url}
            for image in hotel.images
        ]

        # Отримання кімнат готелю
        rooms = []
        for room in hotel.rooms:
            # Отримання зображень кімнати
            room_images = [
                {"id": image.id, "image_url": image.image_url}
                for image in room.images
            ]
            rooms.append({
                "id": room.id,
                "room_number": room.room_number,
                "room_type": room.room_type,
                "places": room.places,
                "price_per_night": room.price_per_night,
                "images": room_images
            })

        result.append({
            "id": hotel.id,
            "name": hotel.name,
            "address": hotel.address,
            "images": hotel_images,
            "rooms": rooms
        })
    return result

@router.get("/")
def get_all_hotels(db: Session = Depends(get_db)):
    return db.query(Hotel).all()

@router.get("/{hotel_id}")
def get_hotel(hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return hotel
@router.delete("/{hotel_id}")
def delete_hotel(hotel_id: int, db: Session = Depends(get_db)):
    try:
        deleted_hotel = crud.delete_record(db, Hotel, hotel_id)
        return deleted_hotel
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
@router.post("/{hotel_id}/images/upload/")
async def upload_hotel_image(
    hotel_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    print("Current User ID:", current_user["id"])
    is_hotel_owner(current_user, hotel_id, db)

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
        hotel_image = crud.add_hotel_image(db, hotel_id=hotel_id, image_url=image_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving image record: {str(e)}")

    return {"id": hotel_image.id, "image_url": image_url}

@router.delete("/images/{image_id}")
def delete_hotel_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    # Отримання зображення
    image = db.query(HotelImage).filter(HotelImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Перевірка на власника
    is_hotel_owner(current_user, image.hotel_id, db)

    file_path = image.image_url.lstrip("/")
    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(image)
    db.commit()
    return {"detail": "Image deleted successfully"}
@router.get("/{hotel_id}/images/")
def get_hotel_images(hotel_id: int, db: Session = Depends(get_db)):
    images = db.query(HotelImage).filter(HotelImage.hotel_id == hotel_id).all()
    return images
