from pydantic import BaseModel

class RoomImageBase(BaseModel):
    id: int
    room_id: int
    image_url: str

    class Config:
        from_attributes = True