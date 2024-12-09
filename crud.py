from sqlalchemy.orm import Session
from models import Person, Owner, Client, Hotel, Room, Booking

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
    db_client = Client(**client)
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

def create_booking(db: Session, booking: dict):
    db_booking = Booking(**booking)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking
