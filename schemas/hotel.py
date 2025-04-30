# schemas/hotel.py

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date

from models import RoomType
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
class HotelSearchParams(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    room_type: Optional[RoomType] = None
    amenity_ids: Optional[List[int]] = None
    has_free_rooms: Optional[bool] = False
    sort_by: Optional[str] = Field("rating", pattern="^(price|rating|views)$")
    sort_dir: Optional[str] = Field("desc", pattern="^(asc|desc)$")
    check_in: Optional[date] = None
    check_out: Optional[date] = None
    skip: int = 0
    limit: int = 25
class FavoriteHotelBase(BaseModel):
    id: int
    hotel_id: int
    client_id: int

    class Config:
        from_attributes = True
