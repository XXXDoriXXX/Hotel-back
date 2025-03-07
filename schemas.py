from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
class HotelImageBase(BaseModel):
    id: int
    hotel_id: int
    image_url: str

    class Config:
        from_attributes = True


class RoomImageBase(BaseModel):
    id: int
    room_id: int
    image_url: str

    class Config:
        from_attributes = True
class ClientDetails(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str]
    phone: str

    class Config:
        from_attributes = True
class PaymentRequest(BaseModel):
    amount: float

class PaymentResponse(BaseModel):
    id: str
    status: str

class BookingDetails(BaseModel):
    id: int
    client_id: int
    client: "ClientDetails"
    date_start: str
    date_end: str
    total_price: float

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat()
        }

class RoomDetails(BaseModel):
    id: int
    room_number: str
    room_type: str
    places: int
    price_per_night: float
    description: Optional[str]
    images: List[RoomImageBase]
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
    rating: float
    rating_count: int
    views: int
    amenities: List[str]
    description: Optional[str]
    images: List[HotelImageBase]
    rooms: List[RoomDetails]
    employees: List[EmployeeDetails]

    class Config:
        from_attributes = True

class PersonBase(BaseModel):
    id: Optional[int] = None  # Робимо id необов'язковим
    first_name: str
    last_name: str
    email: Optional[str]
    phone: str
    is_owner: bool
    birth_date: Optional[date]
    avatar_url: Optional[str] = None  # Робимо avatar_url необов'язковим
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
    rating: Optional[float] = 0.0
    rating_count: Optional[int] = 0
    views: Optional[int] = 0
    amenities: Optional[List[str]] = []
    description: Optional[str] = None

class RoomCreate(BaseModel):
    room_number: str
    room_type: str
    places: int
    price_per_night: float
    hotel_id: int
    description: Optional[str] = None

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

class ChangeCredentialsRequest(BaseModel):
    current_password: str
    new_password: Optional[str] = None
    new_email: Optional[str] = None