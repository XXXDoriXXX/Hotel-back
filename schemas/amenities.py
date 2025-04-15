from typing import Optional

from pydantic import BaseModel


class AmenityBase(BaseModel):
    id: Optional[int] = None
    name: str
    description: str
    is_hotel: bool

    class Config:
        from_attributes = True

class AmenityRoomBase(BaseModel):
    id: int
    room_id: int
    amenity_id: int

    class Config:
        from_attributes = True

class AmenityHotelBase(BaseModel):
    id: int
    hotel_id: int
    amenity_id: int

    class Config:
        from_attributes = True