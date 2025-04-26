from typing import Optional

from pydantic import BaseModel
from datetime import datetime

class BookingCheckoutRequest(BaseModel):
    room_id: int
    date_start: datetime
    date_end: datetime
class RefundRequest(BaseModel):
    reason: Optional[str] = None
class ManualRefundRequest(BaseModel):
    amount: float
class BookingHistoryItem(BaseModel):
    booking_id: int
    hotel_name: str
    room_type: str
    date_start: datetime
    date_end: datetime
    total_price: float
    status: str

    class Config:
        from_attributes = True
