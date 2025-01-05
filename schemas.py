from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
class ClientDetails(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str]
    phone: str

    class Config:
        from_attributes = True

class BookingDetails(BaseModel):
    id: int
    client_id: int
    client: "ClientDetails"
    date_start: str  # Конвертація дати у рядок
    date_end: str  # Конвертація дати у рядок
    total_price: float

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat()  # Автоматичне перетворення об'єкта date у формат YYYY-MM-DD
        }

class RoomDetails(BaseModel):
    id: int
    room_number: str
    room_type: str
    places: int
    price_per_night: float
    bookings: List[BookingDetails]

    class Config:
        from_attributes = True
class EmployeeDetails(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str]
    phone: str
    position: str
    salary: float
    work_experience: int
    is_vacation: bool


class HotelWithDetails(BaseModel):
    id: int
    name: str
    address: str
    rooms: List[RoomDetails]
    employees: List[EmployeeDetails]
    class Config:
        from_attributes = True

class PersonBase(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str]
    phone: str
    is_owner: bool
    birth_date: Optional[date]
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class PersonCreate(PersonBase):
    first_name: str
    last_name: str
    email: Optional[str]
    phone: str
    password: str
    is_owner: Optional[bool] = False
    birth_date: Optional[date]
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
class EmployeeBase(BaseModel):
    position: str
    salary: float
    work_experience: int
    is_vacation: bool = False


class EmployeeCreate(PersonBase):
    hotel_id: int
    position: str
    salary: float
    work_experience: int
    is_vacation: bool

class Employee(EmployeeBase):
    employee_id: int = Field(alias="id")
    person: PersonBase

    class Config:
        from_attributes = True

