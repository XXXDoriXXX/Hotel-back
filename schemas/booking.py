from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from .client import ClientDetails

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