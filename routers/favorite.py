from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from typing import List

from database import get_db
from models import FavoriteHotel, Hotel, Rating
from schemas.hotel import HotelWithImagesAndAddress, HotelWithStats
from dependencies import get_current_user

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.post("/{hotel_id}", status_code=201)
def add_favorite(hotel_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    exists = db.query(FavoriteHotel).filter_by(client_id=user["id"], hotel_id=hotel_id).first()
    if exists:
        raise HTTPException(400, "Hotel already in favorites")

    db.add(FavoriteHotel(client_id=user["id"], hotel_id=hotel_id))
    db.commit()
    return {"message": "Hotel added to favorites"}


@router.delete("/{hotel_id}")
def remove_favorite(hotel_id: int, db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    fav = db.query(FavoriteHotel).filter_by(client_id=user["id"], hotel_id=hotel_id).first()
    if not fav:
        raise HTTPException(404, "Favorite not found")

    db.delete(fav)
    db.commit()
    return {"message": "Hotel removed from favorites"}


@router.get("/", response_model=List[HotelWithStats])
def get_favorites(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    query = (
        db.query(
            Hotel,
            func.coalesce(func.avg(Rating.rating), 0).label("rating"),
            func.coalesce(func.sum(Rating.views), 0).label("views")
        )
        .join(FavoriteHotel, FavoriteHotel.hotel_id == Hotel.id)
        .outerjoin(Rating, Rating.hotel_id == Hotel.id)
        .options(joinedload(Hotel.images), joinedload(Hotel.address))
        .filter(FavoriteHotel.client_id == user["id"])
        .group_by(Hotel.id)
    )

    results = []
    for hotel, rating, views in query.all():
        hotel_schema = HotelWithImagesAndAddress.from_orm(hotel)
        results.append(HotelWithStats(hotel=hotel_schema, rating=rating, views=views))

    return results