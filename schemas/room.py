from pydantic import BaseModel
from typing import List, Optional, TYPE_CHECKING
from datetime import date, datetime

from models import RoomType
from .media import MediaBase
from .room_amenity import RoomAmenityDetails

if TYPE_CHECKING:
    from .booking import BookingDetails

class RoomCreate(BaseModel):
    room_number: str
    room_type: RoomType
    places: int
    price_per_night: float
    hotel_id: int
    description: Optional[str] = None

class RoomDetails(BaseModel):
    id: int
    room_number: str
    room_type: RoomType
    places: int
    price_per_night: float
    description: Optional[str]
    hotel_id: int
    created_at: datetime
    updated_at: datetime
    media: List[MediaBase]
    amenities: List[RoomAmenityDetails]
    bookings: List['BookingDetails']

    class Config:
        from_attributes = True