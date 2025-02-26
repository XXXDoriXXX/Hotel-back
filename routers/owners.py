from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import schemas
from database import get_db
from dependencies import get_current_user
from schemas import OwnerCreate
from models import Owner, Hotel
import crud

router = APIRouter(
    prefix="/owners",
    tags=["owners"]
)

@router.post("/")
def create_owner(owner: OwnerCreate, db: Session = Depends(get_db)):
    db_owner = crud.create_owner(db, owner.dict())
    if not db_owner:
        raise HTTPException(status_code=400, detail="Owner creation failed")
    return db_owner

@router.get("/")
def get_all_owners(db: Session = Depends(get_db)):
    return db.query(Owner).all()
@router.delete("/{owner_id}")
def delete_owner(owner_id: int, db: Session = Depends(get_db)):

    try:
        result = crud.delete_record(db, Owner, owner_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/hotels", response_model=List[schemas.HotelWithDetails])
def get_owner_hotels(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user["is_owner"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    owner = db.query(Owner).filter(Owner.person_id == current_user["id"]).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    hotels = db.query(Hotel).filter(Hotel.owner_id == owner.id).all()

    result = []
    for hotel in hotels:

        rooms = []
        for room in hotel.rooms:
            room_images = [
                {"id": image.id, "room_id": image.room_id, "image_url": image.image_url}
                for image in room.images
            ]
            bookings = [
                {
                    "id": booking.id,
                    "client_id": booking.client_id,
                    "client": {
                        "id": booking.client.person.id,
                        "first_name": booking.client.person.first_name,
                        "last_name": booking.client.person.last_name,
                        "email": booking.client.person.email,
                        "phone": booking.client.person.phone,
                    },
                    "date_start": booking.date_start.isoformat(),
                    "date_end": booking.date_end.isoformat(),
                    "total_price": booking.total_price,
                }
                for booking in room.bookings
            ]
            rooms.append({
                "id": room.id,
                "room_number": room.room_number,
                "room_type": room.room_type,
                "places": room.places,
                "price_per_night": room.price_per_night,
                "images": room_images,
                "bookings": bookings,
            })

        # Отримуємо зображення для готелів
        hotel_images = [
            {"id": image.id, "hotel_id": image.hotel_id, "image_url": image.image_url}
            for image in hotel.images
        ]

        # Додаємо працівників
        employees = [
            {
                "id": employee.id,
                "first_name": employee.person.first_name,
                "last_name": employee.person.last_name,
                "email": employee.person.email,
                "phone": employee.person.phone,
                "position": employee.position,
                "salary": employee.salary,
                "work_experience": employee.work_experience,
                "is_vacation": employee.is_vacation,
            }
            for employee in hotel.employees
        ]

        result.append({
            "id": hotel.id,
            "name": hotel.name,
            "address": hotel.address,
            "images": hotel_images,
            "rooms": rooms,
            "employees": employees,
        })

    return result

@router.post("/hotels/rooms")
def create_room(
    room: schemas.RoomCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user["is_owner"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    return crud.create_room(db, room.dict())

@router.get("/dashboard", response_model=List[schemas.HotelWithDetails])
def get_owner_dashboard(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user["is_owner"]:
        raise HTTPException(status_code=403, detail="Not authorized")

    owner = db.query(Owner).filter(Owner.person_id == current_user["id"]).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    hotels = db.query(Hotel).filter(Hotel.owner_id == owner.id).all()

    dashboard = []
    for hotel in hotels:
        rooms = []
        for room in hotel.rooms:
            room_details = {
                "id": room.id,
                "room_number": room.room_number,
                "room_type": room.room_type,
                "places": room.places,
                "price_per_night": room.price_per_night,
                "images": [
                    {"id": image.id, "room_id": image.room_id, "image_url": image.image_url}
                    for image in room.images
                ],
                "bookings": [
                    {
                        "id": booking.id,
                        "client_id": booking.client_id,
                        "client": {
                            "id": booking.client.person.id,
                            "first_name": booking.client.person.first_name,
                            "last_name": booking.client.person.last_name,
                            "email": booking.client.person.email,
                            "phone": booking.client.person.phone,
                        },
                        "date_start": booking.date_start.isoformat(),
                        "date_end": booking.date_end.isoformat(),
                        "total_price": booking.total_price,
                    }
                    for booking in room.bookings
                ],
            }
            rooms.append(room_details)

        hotel_details = {
            "id": hotel.id,
            "name": hotel.name,
            "address": hotel.address,
            "images": [
                {"id": image.id, "hotel_id": image.hotel_id, "image_url": image.image_url}
                for image in hotel.images
            ],
            "rooms": rooms,
            "employees": [
                {
                    "id": employee.id,
                    "first_name": employee.person.first_name,
                    "last_name": employee.person.last_name,
                    "email": employee.person.email,
                    "phone": employee.person.phone,
                    "position": employee.position,
                    "salary": employee.salary,
                    "work_experience": employee.work_experience,
                    "is_vacation": employee.is_vacation,
                }
                for employee in hotel.employees
            ],
        }
        dashboard.append(hotel_details)

    return dashboard

