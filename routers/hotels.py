import os
from typing import List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from database import get_db
from dependencies import get_current_user, is_hotel_owner
from schemas import HotelCreate, HotelWithDetails
from models import Hotel, HotelImage, Rating
import crud.hotel_crud

router = APIRouter(
    prefix="/hotels",
    tags=["hotels"]
)
UPLOAD_DIRECTORY = "uploaded_images/hotels"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
@router.post("/")
def create_hotel(hotel: HotelCreate, db: Session = Depends(get_db)):
    db_hotel = crud.hotel_crud.create_hotel(db, hotel.dict())
    if not db_hotel:
        raise HTTPException(status_code=400, detail="Hotel creation failed")
    return db_hotel
@router.get("/search", response_model=List[HotelWithDetails])
def search_hotels(
    name: Optional[str] = None,
    address: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Hotel).options(
        joinedload(Hotel.rooms),
        joinedload(Hotel.images),
        joinedload(Hotel.employees)
    )

    if name:
        query = query.filter(Hotel.name.ilike(f"%{name}%"))
    if address:
        query = query.filter(Hotel.address.ilike(f"%{address}%"))

    hotels = query.all()
    if not hotels:
        raise HTTPException(status_code=404, detail="No hotels found")
    return hotels

@router.get("/all_details")
def get_all_hotels_with_details(db: Session = Depends(get_db)):
    hotels = db.query(Hotel).all()
    result = []
    for hotel in hotels:
        hotel_images = [
            {"id": image.id, "image_url": image.image_url}
            for image in hotel.images
        ]
        rooms = []
        for room in hotel.rooms:
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
                "images": room_images,
                "description": room.description
            })

        result.append({
            "id": hotel.id,
            "name": hotel.name,
            "address": hotel.address,
            "images": hotel_images,
            "rooms": rooms,
            "rating":hotel.rating,
            "rating_count":hotel.rating_count,
            "views": hotel.views,
            "description":hotel.description
        })
    return result

@router.get("/")
def get_all_hotels(db: Session = Depends(get_db)):
    return db.query(Hotel).all()

@router.get("/{hotel_id}", response_model=HotelWithDetails)
def get_hotel_by_id(
    hotel_id: int,
    db: Session = Depends(get_db)
):
    hotel = db.query(Hotel).options(
        joinedload(Hotel.rooms),
        joinedload(Hotel.images),
        joinedload(Hotel.employees)
    ).filter(Hotel.id == hotel_id).first()

    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return hotel

@router.delete("/{hotel_id}")
def delete_hotel(hotel_id: int, db: Session = Depends(get_db)):
    try:
        deleted_hotel = crud.hotel_crud.delete_hotel(db, hotel_id)
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
        hotel_image = crud.hotel_crud.create_hotel_image(db, hotel_id=hotel_id, image_url=image_url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving image record: {str(e)}")

    return {"id": hotel_image.id, "image_url": image_url}

@router.delete("/images/{image_id}")
def delete_hotel_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    image = db.query(HotelImage).filter(HotelImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

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
@router.put("/{hotel_id}/amenities")
def update_amenities(
    hotel_id: int,
    amenities: List[str],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    if hotel.owner_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Not authorized to modify this hotel")
    existing_amenities = set(hotel.amenities or [])
    new_amenities = set(amenities)

    if existing_amenities.intersection(new_amenities):
        raise HTTPException(status_code=400, detail="Some amenities already exist")

    hotel.amenities = list(existing_amenities.union(new_amenities))
    db.commit()
    db.refresh(hotel)

    return {
        "message": "Amenities updated successfully",
        "amenities": hotel.amenities
    }
@router.post("/{hotel_id}/view")
def increment_views(
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("is_owner"):
        raise HTTPException(status_code=403, detail="Only clients can add views")

    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    hotel.views += 1
    db.commit()
    db.refresh(hotel)

    return {
        "message": f"Views updated successfully. Total views: {hotel.views}",
        "views": hotel.views
    }
class RatingRequest(BaseModel):
      rating: float

@router.post("/{hotel_id}/rate")
def add_rating(
    hotel_id: int,
    request: RatingRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]
    new_rating = request.rating

    if current_user.get("is_owner"):
        raise HTTPException(status_code=403, detail="Only clients can rate hotels")

    if not (1 <= new_rating <= 5):
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    existing_rating = db.query(Rating).filter(
        Rating.user_id == user_id, Rating.hotel_id == hotel_id
    ).first()

    if existing_rating:
        total_rating = hotel.rating * hotel.rating_count - existing_rating.rating
        total_rating += new_rating
        hotel.rating = total_rating / hotel.rating_count
        existing_rating.rating = new_rating
    else:
        total_rating = hotel.rating * hotel.rating_count
        hotel.rating_count += 1
        hotel.rating = (total_rating + new_rating) / hotel.rating_count

        new_rating_entry = Rating(user_id=user_id, hotel_id=hotel_id, rating=new_rating)
        db.add(new_rating_entry)

    db.commit()
    db.refresh(hotel)

    return {
        "message": "Rating updated successfully",
        "rating": hotel.rating,
        "rating_count": hotel.rating_count
    }
class DescriptionUpdate(BaseModel):
    description: str
@router.put("/{hotel_id}/description")
def update_hotel_description(
    hotel_id: int,
    body: DescriptionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    if hotel.owner_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Not authorized to modify this hotel")

    if len(body.description) > 500:
        raise HTTPException(status_code=400, detail="Description must not exceed 500 characters")

    hotel.description = body.description
    db.commit()
    db.refresh(hotel)
    return {"message": "Hotel description updated successfully"}
