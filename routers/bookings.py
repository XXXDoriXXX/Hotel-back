from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import BookingCreate
from models import Booking, Room
import crud

router = APIRouter(
    prefix="/bookings",
    tags=["bookings"]
)


@router.post("/")
def create_booking(booking: BookingCreate, db: Session = Depends(get_db)):

    room = db.query(Room).filter(Room.id == booking.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    existing_booking = db.query(Booking).filter(
        Booking.room_id == booking.room_id,
        Booking.date_start <= booking.date_end,
        Booking.date_end >= booking.date_start
    ).first()
    if existing_booking:
        raise HTTPException(status_code=400, detail="Room is not available for the selected dates")

    total_days = (booking.date_end - booking.date_start).days
    total_price = total_days * room.price_per_night

    booking_data = booking.dict()
    booking_data["total_price"] = total_price
    db_booking = crud.create_booking(db, booking_data)
    return db_booking


@router.get("/")
def get_all_bookings(db: Session = Depends(get_db)):
    return db.query(Booking).all()


@router.get("/{booking_id}")
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking
@router.delete("/{booking_id}")
def delete_booking(booking_id: int, db: Session = Depends(get_db)):

    try:
        deleted_booking = crud.delete_record(db, Booking, booking_id)
        return deleted_booking
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
