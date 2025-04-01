from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from .room_image import RoomImageBase
from .booking import BookingDetails

class RoomCreate(BaseModel):
    room_number: str
    room_type: str
    places: int
    price_per_night: float
    hotel_id: int
    description: Optional[str] = None

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