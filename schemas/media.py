from datetime import datetime
from enum import Enum

from pydantic import BaseModel



class EntityType(str, Enum):
    HOTEL = "hotel"
    ROOM = "room"
    AVATAR = "avatar"

class MediaBase(BaseModel):
    id: int
    image_url: str
    entity_type: EntityType
    entity_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True