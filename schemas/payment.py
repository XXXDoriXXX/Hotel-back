from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional

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