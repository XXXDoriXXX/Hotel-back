from pydantic import BaseModel
from typing import List, Optional
from .hotel_image import HotelImageBase
from .room import RoomDetails
from .employee import EmployeeDetails

class HotelCreate(BaseModel):
    name: str
    address: str
    owner_id: int
    rating: Optional[float] = 0.0
    rating_count: Optional[int] = 0
    views: Optional[int] = 0
    amenities: Optional[List[str]] = []
    description: Optional[str] = None

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