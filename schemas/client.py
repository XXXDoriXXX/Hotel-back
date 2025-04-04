from pydantic import BaseModel
from typing import Optional
from .person import PersonBase

class ClientCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: str
    password: str

class Client(BaseModel):
    id: int
    person_id: int
    person: PersonBase

    class Config:
        from_attributes = True

class ClientDetails(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str]
    phone: str

    class Config:
        from_attributes = True