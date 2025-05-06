from typing import Optional, List

from pydantic import BaseModel
from datetime import datetime, date

from schemas import HotelImgBase


class BookingCheckoutRequest(BaseModel):
    room_id: int
    payment_method: str
    date_start: datetime
    date_end: datetime
class RefundRequest(BaseModel):
    reason: Optional[str] = None
class ManualRefundRequest(BaseModel):
    amount: float
class BookingHistoryItem(BaseModel):
    booking_id: int
    room_id: int
    room_type: str
    date_start: datetime
    date_end: datetime
    hotel_name: str
    total_price: float
    status: str
    hotel_images: List[HotelImgBase]
    created_at: datetime
    class Config:
        from_attributes = True

class BookingItem(BaseModel):
    room_number: int
    client_name: str
    email: str
    phone: Optional[str]
    is_card: Optional[bool]
    amount: Optional[float]
    period_start: date
    period_end: date
    status: str

    class Config:
        orm_mode = True