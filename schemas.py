from pydantic import BaseModel
from typing import Optional, List
from datetime import date
class BookingDetails(BaseModel):
    id: int
    client_id: int
    date_start: date
    date_end: date
    total_price: float

    class Config:
        from_attributes = True

class RoomDetails(BaseModel):
    id: int
    room_number: str
    room_type: str
    places: int
    price_per_night: float
    bookings: List[BookingDetails] = []

    class Config:
        from_attributes = True

class HotelWithDetails(BaseModel):
    id: int
    name: str
    address: str
    rooms: List[RoomDetails] = []

    class Config:
        from_attributes = True
class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PersonBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str]
    phone: str

class PersonCreate(PersonBase):
    password: str
class OwnerCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: str
    password: str
class Person(PersonBase):
    id: int

    class Config:
        from_attributes = True

class Owner(BaseModel):
    id: int
    person_id: int
    person: PersonBase

    class Config:
        from_attributes = True
class ClientCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: str
    password: str
class Client(BaseModel):
    id: int
    person_id: int
    person: PersonBase

    class Config:
        from_attributes = True

class HotelCreate(BaseModel):
    name: str
    address: str
    owner_id: int

class RoomCreate(BaseModel):
    room_number: str
    room_type: str
    places: int
    price_per_night: float
    hotel_id: int

class BookingCreate(BaseModel):
    client_id: int
    room_id: int
    date_start: date
    date_end: date
    total_price: float
class Booking(BaseModel):
    id: int
    client_id: int
    room_id: int
    date_start: date
    date_end: date
    total_price: float

    class Config:
        from_attributes = True


