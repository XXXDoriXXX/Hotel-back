from pydantic import BaseModel
from datetime import date
from typing import Optional

class PersonBase(BaseModel):
    id: Optional[int] = None
    first_name: str
    last_name: str
    email: Optional[str]
    phone: str
    is_owner: bool
    birth_date: Optional[date]
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True

class PersonCreate(PersonBase):
    first_name: str
    last_name: str
    email: Optional[str]
    phone: str
    password: str
    is_owner: Optional[bool] = False
    birth_date: Optional[date]

class Person(PersonBase):
    id: int

    class Config:
        from_attributes = True