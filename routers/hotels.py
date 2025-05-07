from datetime import datetime, timedelta
from sqlalchemy import Date

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Body, Query
from sqlalchemy import func, extract, case, cast
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import os, uuid, boto3
from database import get_db
from dependencies import get_current_owner, get_current_user
from models import Hotel, HotelImg, Address, Room, Booking, Owner, Payment, AmenityHotel, Rating, BookingStatus, \
    FavoriteHotel, Client, Employee
from schemas.booking import BookingItem
from schemas.hotel import HotelCreate, HotelBase, HotelImgBase, HotelWithImagesAndAddress, HotelWithStats, \
    HotelSearchParams

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


@router.get("/{hotel_id}/bookings", response_model=List[BookingItem])
def get_formatted_bookings(
    hotel_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(25, le=100),
    db: Session = Depends(get_db),
    current_owner = Depends(get_current_owner)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(403, "Not authorized")

    bookings = (
        db.query(Booking)
        .join(Room)
        .options(
            joinedload(Booking.client),
            joinedload(Booking.room),
            joinedload(Booking.payments)
        )
        .filter(Room.hotel_id == hotel_id)
        .order_by(Booking.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for b in bookings:
        first_payment = b.payments[0] if b.payments else None
        result.append({
            "booking_id": b.id,
            "room_number": b.room.room_number,
            "client_name": f"{b.client.first_name} {b.client.last_name}",
            "email": b.client.email,
            "phone": b.client.phone,
            "is_card": first_payment.is_card if first_payment else None,
            "amount": first_payment.amount if first_payment else None,
            "period_start": b.date_start,
            "period_end": b.date_end,
            "status": b.status
        })

    return result
@router.get("/{hotel_id}/stats/full")
def get_advanced_hotel_stats(
    hotel_id: int,
    db: Session = Depends(get_db),
    current_owner = Depends(get_current_owner)
):
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    hotel = db.query(Hotel).filter(Hotel.id == hotel_id, Hotel.owner_id == current_owner.id).first()
    if not hotel:
        raise HTTPException(403, "Not authorized")

    total_rooms_q = db.query(func.count(Room.id)).filter(Room.hotel_id == hotel_id)

    booking_stats_q = db.query(
        func.count(Booking.id),
        func.count(case((Booking.status == 'confirmed', 1))),
        func.count(case((Booking.status == 'completed', 1))),
        func.count(case((Booking.status == 'cancelled', 1)))
    ).join(Room).filter(Room.hotel_id == hotel_id)

    price_stats_q = db.query(
        func.sum(Payment.amount),
        func.sum(case((Payment.is_card == True, Payment.amount))),
        func.sum(case((Payment.is_card == False, Payment.amount))),
        func.sum(case((Payment.status == 'refunded', Payment.amount))),
        func.avg(Payment.amount),
        func.max(Payment.amount),
        func.min(Payment.amount)
    ).join(Payment.booking).join(Booking.room).filter(
        Room.hotel_id == hotel_id, Payment.status == 'paid'
    )

    daily_income_q = db.query(
        cast(Payment.paid_at, Date),
        func.sum(Payment.amount)
    ).join(Payment.booking).join(Booking.room).filter(
        Room.hotel_id == hotel_id, Payment.status == 'paid'
    ).group_by(cast(Payment.paid_at, Date)).order_by(cast(Payment.paid_at, Date))

    weekly_bookings_q = db.query(
        extract("week", Booking.created_at),
        func.count()
    ).join(Room).filter(Room.hotel_id == hotel_id).group_by(extract("week", Booking.created_at))

    room_type_q = db.query(Room.room_type, func.count()).filter(Room.hotel_id == hotel_id).group_by(Room.room_type)

    payment_dist_q = db.query(Payment.is_card, func.count()).join(Payment.booking).join(Booking.room).filter(
        Room.hotel_id == hotel_id, Payment.status == 'paid'
    ).group_by(Payment.is_card)

    unique_clients_q = db.query(func.count(func.distinct(Booking.client_id))).join(Room).filter(Room.hotel_id == hotel_id)

    top_clients_q = db.query(
        Client.id,
        Client.first_name,
        Client.last_name,
        func.sum(Payment.amount)
    ).join(Booking, Client.id == Booking.client_id).join(Payment, Payment.booking_id == Booking.id).join(Room, Booking.room_id == Room.id).filter(
        Room.hotel_id == hotel_id, Payment.status == 'paid'
    ).group_by(Client.id).order_by(func.sum(Payment.amount).desc()).limit(10)

    rating_views_q = db.query(
        func.avg(Rating.rating),
        func.sum(Rating.views)
    ).filter(Rating.hotel_id == hotel_id)

    favorites_q = db.query(func.count()).filter(FavoriteHotel.hotel_id == hotel_id)

    total_rooms = total_rooms_q.scalar()
    bookings_total, bookings_confirmed, bookings_completed, bookings_cancelled = booking_stats_q.one()
    income_total, income_card, income_cash, refunds, avg_price, max_price, min_price = price_stats_q.one()
    daily_income = daily_income_q.all()
    weekly_bookings = weekly_bookings_q.all()
    room_type_stats = room_type_q.all()
    payment_dist = payment_dist_q.all()
    unique_clients = unique_clients_q.scalar()
    top_clients = top_clients_q.all()
    rating_avg, total_views = rating_views_q.one()
    favorites = favorites_q.scalar()
    salary_expenses_q = db.query(func.sum(Employee.salary)).filter(Employee.hotel_id == hotel_id)
    salary_expenses = salary_expenses_q.scalar() or 0

    net_income = (income_total or 0) - salary_expenses
    return {
        "general": {
            "total_rooms": total_rooms,
            "total_bookings": bookings_total,
            "active_bookings": bookings_confirmed,
            "completed_bookings": bookings_completed,
            "cancelled_bookings": bookings_cancelled,
            "occupancy": round(bookings_confirmed / total_rooms, 2) if total_rooms else 0
        },
        "financials": {
            "income_total": income_total or 0,
            "income_card": income_card or 0,
            "income_cash": income_cash or 0,
            "refunds": refunds or 0,
            "avg_booking_price": round(avg_price or 0, 2),
            "max_booking_price": max_price or 0,
            "min_booking_price": min_price or 0,
            "salary_expenses": round(salary_expenses, 2),
            "net_income": round(net_income, 2),
            "income_minus_salaries": round(income_total or 0, 2)
        },
        "dynamics": {
            "daily_income": [{"date": d.isoformat(), "total": float(t)} for d, t in daily_income],
            "weekly_bookings": [{"week": int(w), "count": int(c)} for w, c in weekly_bookings],
            "room_type_popularity": [{"type": rt.value, "count": c} for rt, c in room_type_stats],
            "payment_distribution": {
                "card": next((c for i, c in payment_dist if i), 0),
                "cash": next((c for i, c in payment_dist if not i), 0)
            }
        },
        "clients": {
            "unique": unique_clients,
            "top": [
                {"id": cid, "name": f"{first} {last}", "total_spent": float(spent)}
                for cid, first, last, spent in top_clients
            ]
        },
        "engagement": {
            "average_rating": round(rating_avg or 0, 2),
            "total_views": total_views or 0,
            "favorites": favorites
        }
    }



def build_base_query(db: Session, order_field, join_room=False):
    query = (
        db.query(
            Hotel,
            func.coalesce(func.avg(Rating.rating), 0).label("rating"),
            func.coalesce(func.sum(Rating.views), 0).label("views")
        )
        .join(Rating, Rating.hotel_id == Hotel.id, isouter=True)
        .join(Address, Hotel.address_id == Address.id)
    )

    if join_room:
        query = query.join(Room, Room.hotel_id == Hotel.id)

    return (
        query.options(joinedload(Hotel.images), joinedload(Hotel.address))
        .group_by(Hotel.id)
        .order_by(order_field)
    )

def fetch_hotels(
    db: Session,
    order_field,
    skip: int,
    limit: int,
    city: Optional[str],
    country: Optional[str],
    join_room=False
) -> List[HotelWithStats]:
    query = build_base_query(db, order_field, join_room)

    results = []

    if city:
        city_hotels = (
            query.filter(func.lower(Address.city) == city.lower())
            .offset(skip)
            .limit(limit)
            .all()
        )
        results.extend(city_hotels)

    if len(results) < limit and country:
        remaining = limit - len(results)
        country_hotels = (
            query.filter(
                func.lower(Address.country) == country.lower(),
                func.lower(Address.city) != city.lower()
            )
            .offset(0)
            .limit(remaining)
            .all()
        )
        results.extend(country_hotels)

    if len(results) < limit:
        remaining = limit - len(results)
        world_hotels = (
            query.filter(func.lower(Address.country) != country.lower())
            .offset(0)
            .limit(remaining)
            .all()
        )
        results.extend(world_hotels)

    return [
        HotelWithStats(hotel=h, rating=float(r), views=int(v))
        for h, r, v in results
    ]

@router.get("/trending", response_model=List[HotelWithStats])
def get_trending_hotels(
    skip: int = 0,
    limit: int = 25,
    city: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return fetch_hotels(
        db=db,
        order_field=func.sum(Rating.views).desc(),
        skip=skip,
        limit=limit,
        city=city,
        country=country
    )

@router.get("/popular", response_model=List[HotelWithStats])
def get_popular_hotels(
    skip: int = 0,
    limit: int = 25,
    city: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return fetch_hotels(
        db=db,
        order_field=func.avg(Rating.rating).desc(),
        skip=skip,
        limit=limit,
        city=city,
        country=country
    )

@router.get("/best-deals", response_model=List[HotelWithStats])
def get_best_deals(
    skip: int = 0,
    limit: int = 25,
    city: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return fetch_hotels(
        db=db,
        order_field=func.min(Room.price_per_night).asc(),
        skip=skip,
        limit=limit,
        city=city,
        country=country,
        join_room=True
    )

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

def _base_stats_query(db: Session):
    return (
        db.query(
            Hotel,
            func.coalesce(func.avg(Rating.rating), 0).label("rating"),
            func.coalesce(func.sum(Rating.views), 0).label("views")
        )
        .outerjoin(Rating, Rating.hotel_id == Hotel.id)
        .join(Address, Hotel.address_id == Address.id)
        .join(Room, Room.hotel_id == Hotel.id)
        .options(joinedload(Hotel.images), joinedload(Hotel.address))
        .group_by(Hotel.id)
    )

# ---------------- SEARCH HOTELS ----------------
@router.post("/search", response_model=List[HotelWithStats])
def search_hotels(
    filters: HotelSearchParams,
    db: Session = Depends(get_db)
):
    def normalize(text: str) -> str:
        return text.strip().lower()

    query = _base_stats_query(db)

    if filters.name:
        query = query.filter(func.lower(Hotel.name).like(f"%{normalize(filters.name)}%"))
    if filters.description:
        query = query.filter(func.lower(Hotel.description).like(f"%{normalize(filters.description)}%"))
    if filters.city:
        query = query.filter(func.lower(Address.city).like(f"%{normalize(filters.city)}%"))
    if filters.state:
        query = query.filter(func.lower(Address.state).like(f"%{normalize(filters.state)}%"))
    if filters.country:
        query = query.filter(func.lower(Address.country).like(f"%{normalize(filters.country)}%"))
    if filters.postal_code:
        query = query.filter(func.lower(Address.postal_code).like(f"%{normalize(filters.postal_code)}%"))

    if filters.min_price is not None:
        query = query.filter(Room.price_per_night >= filters.min_price)
    if filters.max_price is not None:
        query = query.filter(Room.price_per_night <= filters.max_price)

    if filters.min_rating is not None:
        query = query.having(func.avg(Rating.rating) >= filters.min_rating)

    if filters.room_type:
        query = query.filter(Room.room_type == filters.room_type)

    if filters.amenity_ids:
        query = query.join(AmenityHotel).filter(AmenityHotel.amenity_id.in_(filters.amenity_ids))

    if filters.check_in and filters.check_out:
        if filters.check_in >= filters.check_out:
            raise HTTPException(400, detail="check_in must be before check_out")

        subq = (
            db.query(Booking.room_id)
            .filter(
                Booking.status == BookingStatus.confirmed,
                Booking.date_end > filters.check_in,
                Booking.date_start < filters.check_out
            )
            .subquery()
        )
        query = query.filter(~Room.id.in_(subq))

    sort_map = {
        "price": func.min(Room.price_per_night),
        "rating": func.avg(Rating.rating),
        "views": func.sum(Rating.views)
    }
    sort_field = sort_map.get(filters.sort_by, func.avg(Rating.rating))
    query = query.order_by(sort_field.desc() if filters.sort_dir == "desc" else sort_field.asc())

    results = query.offset(filters.skip).limit(filters.limit).all()

    return [HotelWithStats(hotel=h, rating=float(r), views=int(v)) for h, r, v in results]

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
            joinedload(Hotel.address),
            joinedload(Hotel.owner)
        )
        .filter(Hotel.id == hotel_id)
        .first()
    )

    if not hotel:
        raise HTTPException(404, "Hotel not found")

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

    hotel_with_flag = HotelWithImagesAndAddress.from_orm(hotel)
    hotel_with_flag.is_card_available = bool(hotel.owner.stripe_account_id)

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
        "hotel": hotel_with_flag,
        "rating": float(rating),
        "views": int(views)
    }
