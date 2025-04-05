from typing import Optional

from pydantic import BaseModel

class AmenityDetails(BaseModel):
    id: int
    name: str
    description: Optional[str]
    icon_url: str

    class Config:
        from_attributes = True