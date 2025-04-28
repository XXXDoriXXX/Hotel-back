from datetime import date

from pydantic import BaseModel
from typing import Optional, List
from models import RoomType


class RoomCreate(BaseModel):
    room_number: str
    room_type: RoomType
    places: int
    price_per_night: float
    hotel_id: int
    description: Optional[str]


class RoomBase(RoomCreate):
    id: int

    class Config:
        from_attributes = True


class RoomImgBase(BaseModel):
    id: int
    room_id: int
    image_url: str

    class Config:
        from_attributes = True



class AmenityRoomBase(BaseModel):
    id: int
    room_id: int
    amenity_id: int

    class Config:
        from_attributes = True
class RoomDetails(RoomBase):
    images: List[RoomImgBase] = []
    amenities: List[AmenityRoomBase] = []
class RoomCreateRequest(BaseModel):
    room_number: str
    room_type: RoomType
    places: int
    price_per_night: float
    hotel_id: int
    description: Optional[str]
    amenity_ids: Optional[List[int]] = None
class RoomWithAmenities(RoomBase):
    amenities: List[AmenityRoomBase] = []

class BookedDate(BaseModel):
    start_date: date
    end_date: date