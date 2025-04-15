from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Amenity, AmenityRoom, AmenityHotel

from schemas.amenities import AmenityBase, AmenityRoomBase, AmenityHotelBase

router = APIRouter(prefix="/amenities", tags=["amenities"])
@router.get("/hotel", response_model=List[AmenityBase])
def get_hotel_amenities(db: Session = Depends(get_db)):
    query = db.query(Amenity).filter(Amenity.is_hotel == True)
    amenities = query.all()
    return amenities
@router.get("/room", response_model=List[AmenityBase])
def get_room_amenities(db: Session = Depends(get_db)):
    query = (
        db.query(Amenity).filter(Amenity.is_hotel == False)
    )
    amenities = query.all()
    return amenities
@router.post("/", response_model=AmenityBase, status_code=201)
def create_amenities(
    amenities_data: AmenityBase,
    db: Session = Depends(get_db)
):
    new_amenity = Amenity(
        name=amenities_data.name,
        description=amenities_data.description,
        is_hotel=amenities_data.is_hotel
    )
    db.add(new_amenity)
    db.commit()
    db.refresh(new_amenity)
    return new_amenity