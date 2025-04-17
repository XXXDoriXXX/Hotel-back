from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Body
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import os, uuid, boto3
from database import get_db
from dependencies import get_current_owner, get_current_user
from models import Hotel, HotelImg, Address, Room, Booking, Owner, Payment, AmenityHotel, Rating
from schemas.hotel import HotelCreate, HotelBase, HotelImgBase, HotelWithImagesAndAddress, HotelWithStats

router = APIRouter(prefix="/hotels", tags=["hotels"])

S3_BUCKET = os.getenv('S3_BUCKET')
S3_REGION = os.getenv('S3_REGION')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

s3_client = boto3.client(
    's3',
    region_name=S3_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# ---------------- CREATE HOTEL ----------------
@router.post("/", response_model=HotelBase, status_code=201)
def create_hotel(
    hotel_data: HotelCreate,
    db: Session = Depends(get_db),
    current_owner = Depends(get_current_owner)
):
    addr_data = hotel_data.address.dict()
    address = Address(**addr_data)
    db.add(address)
    db.commit()
    db.refresh(address)

    hotel = Hotel(
        name=hotel_data.name,
        description=hotel_data.description,
        owner_id=current_owner.id,
        address_id=address.id
    )
    db.add(hotel)
    db.commit()
    db.refresh(hotel)
    return hotel
# ---------------- GET MY HOTEL ----------------
@router.get("/my", response_model=List[HotelWithImagesAndAddress])
def get_owner_hotels(
    db: Session = Depends(get_db),
    current_owner = Depends(get_current_owner)
):
    hotels = (
        db.query(Hotel)
        .options(
            joinedload(Hotel.images),
            joinedload(Hotel.address)
        )
        .filter(Hotel.owner_id == current_owner.id)
        .all()
    )
    return hotels



# ---------------- GET ALL HOTELS ----------------
@router.get("/", response_model=List[HotelBase])
def get_all_hotels(db: Session = Depends(get_db)):
    return db.query(Hotel).all()
# ---------------- UPDATE HOTEL ----------------
@router.put("/{hotel_id}", response_model=HotelBase)
def update_hotel(
    hotel_id: int,
    amenity_ids: List[int] = Body(...),
    hotel_data: HotelCreate = Body(...),
    db: Session = Depends(get_db),
    current_owner=Depends(get_current_owner)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    if hotel.owner_id != current_owner.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this hotel")

    hotel.name = hotel_data.name
    hotel.description = hotel_data.description
    db.query(AmenityHotel).filter(AmenityHotel.hotel_id == hotel_id).delete()

    for amenity_id in amenity_ids:
        db.add(AmenityHotel(hotel_id=hotel_id, amenity_id=amenity_id))
    if hotel_data.address:
        address = db.query(Address).filter(Address.id == hotel.address_id).first()
        if address:
            for key, value in hotel_data.address.dict().items():
                setattr(address, key, value)

    db.commit()
    db.refresh(hotel)
    return hotel
# ---------------- DELETE HOTEL ----------------
@router.delete("/{hotel_id}")
def delete_hotel(hotel_id: int, db: Session = Depends(get_db), current_owner = Depends(get_current_owner)):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(404, "Hotel not found")
    if hotel.owner_id != current_owner.id:
        raise HTTPException(403, "You are not the owner of this hotel")
    db.delete(hotel)
    db.commit()
    return {"message": "Hotel deleted"}

# ---------------- UPLOAD HOTEL IMAGE ----------------
@router.post("/{hotel_id}/images", response_model=HotelImgBase)
async def upload_image(
    hotel_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_owner = Depends(get_current_owner)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(404, "Hotel not found or no access")

    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "webp"]:
        raise HTTPException(400, "Invalid image format")

    filename = f"{uuid.uuid4()}.{ext}"
    s3_key = f"hotels/{hotel_id}/{filename}"
    try:
        s3_client.upload_fileobj(
            file.file, S3_BUCKET, s3_key,
            ExtraArgs={
                "ContentType": file.content_type
            }
        )
        url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        image = HotelImg(hotel_id=hotel_id, image_url=url)
        db.add(image)
        db.commit()
        db.refresh(image)
        return image
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")

# ---------------- GET HOTEL IMAGES ----------------
@router.get("/{hotel_id}/images", response_model=List[HotelImgBase])
def get_images(hotel_id: int, db: Session = Depends(get_db)):
    return db.query(HotelImg).filter(HotelImg.hotel_id == hotel_id).all()

# ---------------- DELETE HOTEL IMAGE ----------------
@router.delete("/images/{image_id}")
def delete_image(image_id: int, db: Session = Depends(get_db), current_owner = Depends(get_current_owner)):
    image = db.query(HotelImg).filter(HotelImg.id == image_id).first()
    if not image:
        raise HTTPException(404, "Image not found")
    hotel = db.query(Hotel).filter(Hotel.id == image.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(403, "Not authorized")

    s3_key = image.image_url.split(f"{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/")[-1]
    s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)

    db.delete(image)
    db.commit()
    return {"message": "Image deleted"}


@router.get("/{hotel_id}/stats")
def get_hotel_stats(
        hotel_id: int,
        db: Session = Depends(get_db),
        current_owner: Owner = Depends(get_current_owner)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(403, "Not authorized")

    room_count = db.query(Room).filter(Room.hotel_id == hotel_id).count()

    booking_count = db.query(Booking).filter(
        Booking.status == "confirmed",
        Booking.room.has(Room.hotel_id == hotel_id),
        Booking.date_end >= datetime.now()
    ).count()

    income = db.query(func.sum(Payment.amount)).join(
        Payment.booking
    ).join(
        Booking.room
    ).filter(
        Payment.status == "paid",
        Room.hotel_id == hotel_id
    ).scalar() or 0

    total_rooms = room_count
    booked_rooms = booking_count

    occupancy = booked_rooms / total_rooms if total_rooms > 0 else 0

    return {
        "rooms": room_count,
        "bookings": booking_count,
        "income": income,
        "occupancy": round(occupancy, 2)
    }
@router.get("/trending", response_model=List[HotelWithStats])
def get_trending_hotels(
    skip: int = 0,
    limit: int = 25,
    city: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    def build_query():
        return (
            db.query(
                Hotel,
                func.coalesce(func.avg(Rating.rating), 0).label("rating"),
                func.coalesce(func.sum(Rating.views), 0).label("views")
            )
            .join(Rating, Rating.hotel_id == Hotel.id, isouter=True)
            .join(Address, Hotel.address_id == Address.id)
            .options(joinedload(Hotel.images), joinedload(Hotel.address))
            .group_by(Hotel.id)
            .order_by(func.sum(Rating.views).desc())
        )

    results = []

    if city:
        city_hotels = (
            build_query()
            .filter(func.lower(Address.city) == city.lower())
            .offset(skip)
            .limit(limit)
            .all()
        )
        results.extend(city_hotels)

    if len(results) < limit and country:
        remaining = limit - len(results)
        country_hotels = (
            build_query()
            .filter(func.lower(Address.country) == country.lower())
            .filter(func.lower(Address.city) != city.lower())
            .offset(0)
            .limit(remaining)
            .all()
        )
        results.extend(country_hotels)

    if len(results) < limit:
        remaining = limit - len(results)
        all_hotels = (
            build_query()
            .filter(func.lower(Address.country) != country.lower())
            .offset(0)
            .limit(remaining)
            .all()
        )
        results.extend(all_hotels)

    return [
        HotelWithStats(hotel=h, rating=float(r), views=int(v))
        for h, r, v in results
    ]

@router.get("/popular", response_model=List[HotelWithStats])
def get_popular_hotels(
    skip: int = 0,
    limit: int = 25,
    city: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    def build_query():
        return (
            db.query(
                Hotel,
                func.coalesce(func.avg(Rating.rating), 0).label("rating"),
                func.coalesce(func.sum(Rating.views), 0).label("views")
            )
            .join(Rating, Rating.hotel_id == Hotel.id, isouter=True)
            .join(Address, Hotel.address_id == Address.id)
            .options(joinedload(Hotel.images), joinedload(Hotel.address))
            .group_by(Hotel.id)
            .order_by(func.avg(Rating.rating).desc())
        )

    results = []

    if city:
        city_hotels = (
            build_query()
            .filter(func.lower(Address.city) == city.lower())
            .offset(skip)
            .limit(limit)
            .all()
        )
        results.extend(city_hotels)

    if len(results) < limit and country:
        remaining = limit - len(results)
        country_hotels = (
            build_query()
            .filter(func.lower(Address.country) == country.lower())
            .filter(func.lower(Address.city) != city.lower())
            .offset(0).limit(remaining).all()
        )
        results.extend(country_hotels)

    if len(results) < limit:
        remaining = limit - len(results)
        all_hotels = (
            build_query()
            .filter(func.lower(Address.country) != country.lower())
            .offset(0).limit(remaining).all()
        )
        results.extend(all_hotels)

    return [
        HotelWithStats(hotel=h, rating=float(r), views=int(v))
        for h, r, v in results
    ]


@router.get("/best-deals", response_model=List[HotelWithStats])
def get_best_deals(
    skip: int = 0,
    limit: int = 25,
    city: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    def build_query():
        return (
            db.query(
                Hotel,
                func.coalesce(func.avg(Rating.rating), 0).label("rating"),
                func.coalesce(func.sum(Rating.views), 0).label("views")
            )
            .join(Room, Room.hotel_id == Hotel.id)
            .join(Rating, Rating.hotel_id == Hotel.id, isouter=True)
            .join(Address, Hotel.address_id == Address.id)
            .options(joinedload(Hotel.images), joinedload(Hotel.address))
            .group_by(Hotel.id)
            .order_by(func.min(Room.price_per_night).asc())
        )

    results = []

    if city:
        city_hotels = (
            build_query()
            .filter(func.lower(Address.city) == city.lower())
            .offset(skip)
            .limit(limit)
            .all()
        )
        results.extend(city_hotels)

    if len(results) < limit and country:
        remaining = limit - len(results)
        country_hotels = (
            build_query()
            .filter(func.lower(Address.country) == country.lower())
            .filter(func.lower(Address.city) != city.lower())
            .offset(0).limit(remaining).all()
        )
        results.extend(country_hotels)

    if len(results) < limit:
        remaining = limit - len(results)
        all_hotels = (
            build_query()
            .filter(func.lower(Address.country) != country.lower())
            .offset(0).limit(remaining).all()
        )
        results.extend(all_hotels)

    return [
        HotelWithStats(hotel=h, rating=float(r), views=int(v))
        for h, r, v in results
    ]
@router.put("/{hotel_id}/rate")
def rate_hotel(
    hotel_id: int,
    value: float = Body(..., gt=0.4, le=5.0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("is_owner"):
        raise HTTPException(403, detail="Only clients can rate hotels")

    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(404, detail="Hotel not found")

    rating = (
        db.query(Rating)
        .filter(Rating.hotel_id == hotel_id, Rating.user_id == current_user["id"])
        .first()
    )

    if rating:
        rating.rating = value
    else:
        rating = Rating(hotel_id=hotel_id, user_id=current_user["id"], rating=value, views=1)
        db.add(rating)

    db.commit()
    return {"message": "Rating submitted"}


# ---------------- GET HOTEL BY ID ----------------
@router.get("/{hotel_id}", response_model=HotelWithStats)
def get_hotel(
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    hotel = (
        db.query(Hotel)
        .options(
            joinedload(Hotel.images),
            joinedload(Hotel.amenities),
            joinedload(Hotel.address)
        )
        .filter(Hotel.id == hotel_id)
        .first()
    )

    if not hotel:
        raise HTTPException(404, "Hotel not found")

    # Calculate rating and views
    rating = (
        db.query(func.coalesce(func.avg(Rating.rating), 0))
        .filter(Rating.hotel_id == hotel_id)
        .scalar()
    )
    views = (
        db.query(func.coalesce(func.sum(Rating.views), 0))
        .filter(Rating.hotel_id == hotel_id)
        .scalar()
    )

    if not current_user.get("is_owner"):
        user_rating = (
            db.query(Rating)
            .filter(Rating.hotel_id == hotel_id, Rating.user_id == current_user["id"])
            .first()
        )
        if user_rating:
            user_rating.views += 1
        else:
            db.add(Rating(
                hotel_id=hotel_id,
                user_id=current_user["id"],
                rating=0.0,
                views=1
            ))
        db.commit()

    return {
        "hotel": hotel,
        "rating": float(rating),
        "views": int(views)
    }