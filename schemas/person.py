from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from .media import MediaBase


class PersonBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    is_owner: bool = False
    birth_date: Optional[date] = None


    class Config:
        from_attributes = True

class PersonCreate(PersonBase):
    password: str

class Person(PersonBase):
    id: int
    created_at: datetime
    updated_at: datetime
    media: list[MediaBase] = []

    @property
    def avatar(self) -> Optional[MediaBase]:
        return next((m for m in self.media if m.entity_type == "avatar"), None)

    class Config:
        from_attributes = True