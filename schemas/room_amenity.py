from typing import Optional

from pydantic import BaseModel
from .amenity import AmenityDetails

class RoomAmenityDetails(BaseModel):
    id: int
    is_paid: bool
    quantity: int
    price: Optional[float]
    amenity: AmenityDetails

    class Config:
        from_attributes = True