from pydantic import BaseModel, EmailStr
from datetime import datetime
class ClientCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str
    birth_date: datetime


class OwnerCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"