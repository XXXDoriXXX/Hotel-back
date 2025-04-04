from pydantic import BaseModel, validator
from datetime import date, datetime
from typing import Optional

from models import PaymentMethod
from .client import ClientDetails

class BookingCreate(BaseModel):
    client_id: int
    room_id: int
    date_start: date
    date_end: date
    payment_method: PaymentMethod
@validator('date_end')
def validate_dates(cls, v, values):
    if 'date_start' in values and v <= values['date_start']:
        raise ValueError('End date must be after start date')
    return v
class BookingResponse(BaseModel):
    id: int
    status: str
    payment_status: str

class Booking(BaseModel):
    id: int
    client_id: int
    room_id: int
    date_start: date
    date_end: date
    total_price: float

    class Config:
        from_attributes = True

class BookingDetails(BaseModel):
    id: int
    client_id: int
    client: ClientDetails
    date_start: str
    date_end: str
    total_price: float
    payment_id: Optional[int] = None
    status: str
    created_at: datetime
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat()
        }