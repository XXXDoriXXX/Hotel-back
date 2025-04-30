from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import FavoriteHotel, Hotel
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
def get_favorites(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    favorites = (
        db.query(Hotel)
        .join(FavoriteHotel, FavoriteHotel.hotel_id == Hotel.id)
        .filter(FavoriteHotel.client_id == user["id"])
        .all()
    )
    return favorites
