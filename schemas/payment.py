from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional

from sqlalchemy import Enum

from schemas import BookingCreate


class PaymentIntentRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount must be positive")
    booking_data: BookingCreate

class PaymentIntentResponse(BaseModel):
    payment_intent_id: str
    client_secret: str
    status: str

class PaymentRequest(BaseModel):
    amount: float

class PaymentResponse(BaseModel):
    id: str
    clientSecret: str
    status: str

class PaymentSuccessRequest(BaseModel):
    client_id: int
    room_id: int
    date_start: date
    date_end: date
    total_price: float
    amount: float

class PaymentBase(BaseModel):
    id: int
    amount: float
    status: str
    created_at: datetime
    paid_at: Optional[datetime]

    class Config:
        from_attributes = True

class PaymentIntentCreate(BaseModel):
    booking_id: int
    payment_method_id: str
