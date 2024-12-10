from sqlalchemy.orm import Session
from models import Person, Owner, Client, Hotel, Room, Booking
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_

def create_person(db: Session, person: dict):
    db_person = Person(**person)
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person

def create_owner(db: Session, owner_data: dict):
    # Створення запису в таблиці Person
    db_person = Person(
        first_name=owner_data["first_name"],
        last_name=owner_data["last_name"],
        email=owner_data["email"],
        phone=owner_data["phone"],
    )
    db.add(db_person)
    db.commit()
    db.refresh(db_person)

    # Створення запису в таблиці Owner
    db_owner = Owner(person_id=db_person.id)
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)

    return db_owner


def create_client(db: Session, client: dict):
    db_person = Person(
        first_name=client["first_name"],
        last_name=client["last_name"],
        email=client["email"],
        phone=client["phone"],
    )
    db.add(db_person)
    db.commit()
    db.refresh(db_person)

    db_client = Client(person_id=db_person.id)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)

    return db_client

def create_hotel(db: Session, hotel: dict):
    db_hotel = Hotel(**hotel)
    db.add(db_hotel)
    db.commit()
    db.refresh(db_hotel)
    return db_hotel

def create_room(db: Session, room: dict):
    db_room = Room(**room)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def create_booking(db: Session, booking_data: dict):
    # Перевірка доступності кімнати
    overlapping_bookings = db.query(Booking).filter(
        Booking.room_id == booking_data.get("room_id"),
        and_(
            Booking.date_start <= booking_data.get("date_end"),
            Booking.date_end >= booking_data.get("date_start")
        )
    ).first()

    if overlapping_bookings:
        raise ValueError(f"Room {booking_data.get('room_id')} is already booked for the selected dates: "
                         f"{overlapping_bookings.date_start} to {overlapping_bookings.date_end}.")

    # Створення бронювання
    try:
        db_booking = Booking(
            client_id=booking_data.get("client_id"),
            room_id=booking_data.get("room_id"),
            date_start=booking_data.get("date_start"),
            date_end=booking_data.get("date_end"),
            total_price=booking_data.get("total_price"),
        )
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        return db_booking
    except Exception as e:
        db.rollback()
        raise ValueError(f"Error creating booking: {str(e)}")
def delete_record(db: Session, model, record_id: int):
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise ValueError(f"Record with id {record_id} not found.")
    db.delete(record)
    db.commit()
    return record
