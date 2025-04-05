from pydantic import BaseModel, validator
from datetime import date, datetime
from typing import Optional, TYPE_CHECKING

from models import PaymentMethod, PaymentStatus
from .client import Client
from .payment import PaymentDetails

if TYPE_CHECKING:
    from .room import RoomDetails

class BookingCreate(BaseModel):
    client_id: int
    room_id: int
    date_start: date
    date_end: date
    guests_count: int = 1

    @validator('date_end')
    def validate_dates(cls, v, values):
        if 'date_start' in values and v <= values['date_start']:
            raise ValueError('End date must be after start date')
        return v

class BookingDetails(BaseModel):
    id: int
    client: Client
    room: 'RoomDetails'
    date_start: date
    date_end: date
    guests_count: int
    total_price: float
    status: str
    payment: Optional[PaymentDetails] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookingResponse(BaseModel):
    id: int
    room_id: int
    client_id: int
    date_start: date
    date_end: date
    guests_count: int
    total_price: float
    status: str
    payment_method: PaymentMethod
    payment_status: PaymentStatus
    confirmation_number: str
    created_at: str