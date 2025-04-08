# schemas/hotel.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class AddressCreate(BaseModel):
    street: str
    city: str
    state: Optional[str]
    country: str
    postal_code: str
    latitude: Optional[float]
    longitude: Optional[float]


class HotelCreate(BaseModel):
    name: str
    description: Optional[str] = None
    address: AddressCreate

class HotelBase(BaseModel):
    id: int
    name: str
    address_id: int
    owner_id: int
    description: Optional[str] = None

    class Config:
        from_attributes = True


class HotelImgBase(BaseModel):
    id: int
    hotel_id: int
    image_url: str

    class Config:
        from_attributes = True


class AmenityHotelBase(BaseModel):
    id: int
    hotel_id: int
    amenity_id: int

    class Config:
        from_attributes = True


class HotelWithImages(HotelBase):
    images: List[HotelImgBase] = []


class HotelWithAmenities(HotelBase):
    amenities: List[AmenityHotelBase] = []


class HotelWithAll(HotelBase):
    images: List[HotelImgBase] = []
    amenities: List[AmenityHotelBase] = []
