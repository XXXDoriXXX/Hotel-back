from pydantic import BaseModel

class HotelImageBase(BaseModel):
    id: int
    hotel_id: int
    image_url: str

    class Config:
        from_attributes = True