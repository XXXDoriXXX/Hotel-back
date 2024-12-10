from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import HotelCreate
from models import Hotel
import crud

router = APIRouter(
    prefix="/hotels",
    tags=["hotels"]
)

@router.post("/")
def create_hotel(hotel: HotelCreate, db: Session = Depends(get_db)):
    db_hotel = crud.create_hotel(db, hotel.dict())
    if not db_hotel:
        raise HTTPException(status_code=400, detail="Hotel creation failed")
    return db_hotel

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
