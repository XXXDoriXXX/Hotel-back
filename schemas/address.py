from typing import Optional

from pydantic import BaseModel

class AddressDetails(BaseModel):
    id: int
    street: str
    city: str
    state: Optional[str]
    country: str
    postal_code: str
    latitude: Optional[float]
    longitude: Optional[float]

    class Config:
        from_attributes = True