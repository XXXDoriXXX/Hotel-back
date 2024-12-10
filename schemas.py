from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class PersonBase(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str]
    phone: str

class PersonCreate(PersonBase):
    pass
class OwnerCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: str

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
