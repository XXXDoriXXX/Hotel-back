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
class ClientOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str

    class Config:
        orm_mode = True

class PaymentOut(BaseModel):
    id: int
    amount: float
    is_card: bool
    status: str

    class Config:
        orm_mode = True

class BookingOut(BaseModel):
    id: int
    status: str
    date_start: date
    date_end: date
    room_id: int
    client: ClientOut
    payment: Optional[PaymentOut]

    class Config:
        orm_mode = True
