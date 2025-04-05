from pydantic import BaseModel
from typing import Optional
from .person import PersonBase

class OwnerCreate(BaseModel):
    person_id: int

class Owner(BaseModel):
    id: int
    person: PersonBase
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True