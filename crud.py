import os

from sqlalchemy.orm import Session
from models import Person, Owner, Client, Hotel, Room, Booking, Employee, HotelImage, RoomImage, Payment
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password):
    return pwd_context.hash(password)
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
def add_hotel_image(db: Session, hotel_id: int, image_url: str):
    hotel_image = HotelImage(hotel_id=hotel_id, image_url=image_url)
    db.add(hotel_image)
    db.commit()
    db.refresh(hotel_image)
    return hotel_image


def add_room_image(db: Session, room_id: int, image_url: str):
    room_image = RoomImage(room_id=room_id, image_url=image_url)
    db.add(room_image)
    db.commit()
    db.refresh(room_image)
    return room_image

def authenticate_user(db: Session, email: str, password: str):
    person = db.query(Person).filter(Person.email == email).first()
    if not person or not verify_password(password, person.password):
        return None
    owner_id = None
    if person.is_owner:
        owner = db.query(Owner).filter(Owner.person_id == person.id).first()
        owner_id = owner.id if owner else None
    return {
        "id": person.id,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "email": person.email,
        "phone": person.phone,
        "is_owner": person.is_owner,
        "birth_date": person.birth_date,
        "owner_id": owner_id
    }


def create_person(db: Session, person: dict):
    existing_user = db.query(Person).filter(
        (Person.email == person.get("email")) |
        (Person.phone == person.get("phone"))
    ).first()

    if existing_user:
        raise ValueError("User with the same email or phone already exists.")

    hashed_password = get_password_hash(person.get("password"))

    db_person = Person(
        first_name=person.get("first_name"),
        last_name=person.get("last_name"),
        email=person.get("email"),
        phone=person.get("phone"),
        password=hashed_password,
        is_owner=person.get("is_owner", False),
        birth_date=person.get("birth_date")
    )
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person


def create_owner(db: Session, owner_data: dict):
    owner_data["is_owner"] = True
    person = create_person(db, owner_data)
    db_owner = Owner(person_id=person.id)
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)

    return db_owner


def create_client(db: Session, client: dict):
    person = create_person(db, client)
    db_client = Client(person_id=person.id)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)

    return db_client

def create_hotel(db: Session, hotel: dict):
    db_hotel = Hotel(
        name=hotel["name"],
        address=hotel["address"],
        owner_id=hotel["owner_id"],
        rating=hotel.get("rating", 0.0),
        rating_count=hotel.get("rating_count", 0),
        views=hotel.get("views", 0),
        amenities=hotel.get("amenities", []),
        description=hotel.get("description", None)
    )
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


def create_employee(db: Session, employee_data: dict):
    existing_person = db.query(Person).filter(Person.email == employee_data.get("email")).first()
    if existing_person:
        raise ValueError(f"Person with email {employee_data.get('email')} already exists.")

    db_person = Person(
        first_name=employee_data["first_name"],
        last_name=employee_data["last_name"],
        email=employee_data.get("email"),
        phone=employee_data["phone"],
        password=get_password_hash(employee_data.get("password", "default_password")),
        birth_date=employee_data.get("birth_date")
    )
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    db_employee = Employee(
        person_id=db_person.id,
        hotel_id=employee_data["hotel_id"],
        position=employee_data["position"],
        salary=employee_data["salary"],
        work_experience=employee_data["work_experience"],
        is_vacation=employee_data["is_vacation"]
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee


def delete_employee(db: Session, employee_id: int):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError(f"Employee with id {employee_id} not found.")
    db.delete(employee.person)
    db.commit()
    return employee


def create_booking(db: Session, booking_data: dict):
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
def delete_room_image(db: Session, image_id: int):

    image = db.query(RoomImage).filter(RoomImage.id == image_id).first()
    if not image:
        raise ValueError("Image not found")

    file_path = image.image_url.lstrip("/")
    if os.path.exists(file_path):
        os.remove(file_path)
    db.delete(image)
    db.commit()
def create_payment(db: Session, payment_data: dict):
    db_payment = Payment(
        amount=payment_data.get("amount"),
        status=payment_data.get("status"),
        paid_at=payment_data.get("paid_at")
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment
