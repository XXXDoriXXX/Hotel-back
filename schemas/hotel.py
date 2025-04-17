# schemas/hotel.py

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from schemas.amenities import AmenityHotelBase


class AddressCreate(BaseModel):
    street: str
    city: str
    state: Optional[str]
    country: str
    postal_code: str
    latitude: Optional[float]
    longitude: Optional[float]

class AddressBase(BaseModel):
    street: str
    city: str
    state: str | None = None
    country: str
    postal_code: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    class Config:
        from_attributes = True
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




class HotelWithImagesAndAddress(HotelBase):
    images: list[HotelImgBase] = []
    address: AddressBase
    amenities: List[AmenityHotelBase] = []

    class Config:
        from_attributes = True
class HotelWithStats(BaseModel):
    hotel: HotelWithImagesAndAddress
    rating: float
    views: int

class HotelWithAmenities(HotelBase):
    amenities: List[AmenityHotelBase] = []


class HotelWithAll(HotelBase):
    images: List[HotelImgBase] = []
    amenities: List[AmenityHotelBase] = []
