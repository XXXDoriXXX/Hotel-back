from pydantic import BaseModel
from typing import List, Optional

from pydantic.v1 import Field

from .media import MediaBase
from .address import AddressDetails
from .amenity import AmenityDetails
from .room import RoomDetails
from .employee import EmployeeDetails

class HotelCreate(BaseModel):
    name: str
    address_id: int
    description: Optional[str] = None
class HotelWithDetails(BaseModel):
    id: int
    name: str
    address: AddressDetails
    owner_id: int
    views: int
    description: Optional[str]
    created_at: str
    updated_at: str
    media: List[MediaBase]
    rooms: List[RoomDetails]
    employees: List[EmployeeDetails]
    amenities: List[AmenityDetails]

    class Config:
        from_attributes = True
class HotelAmenitiesUpdate(BaseModel):
    amenities: List[str] = Field(..., min_items=1)