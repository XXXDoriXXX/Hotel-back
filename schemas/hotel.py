from pydantic import BaseModel
from typing import List, Optional

from pydantic.v1 import Field

from .hotel_image import HotelImageBase
from .room import RoomDetails
from .employee import EmployeeDetails

class HotelCreate(BaseModel):
    name: str
    address: str
    rating: Optional[float] = 0.0
    rating_count: Optional[int] = 0
    views: Optional[int] = 0
    amenities: Optional[List[str]] = []
    description: Optional[str] = None
    class Config:
        from_attributes = True

class HotelWithDetails(BaseModel):
    id: int
    name: str
    address: str
    rating: float
    rating_count: int
    views: int
    amenities: List[str]
    description: Optional[str]
    images: List[HotelImageBase]
    rooms: List[RoomDetails]
    employees: List[EmployeeDetails]

    class Config:
        from_attributes = True
class HotelAmenitiesUpdate(BaseModel):
    amenities: List[str] = Field(..., min_items=1)