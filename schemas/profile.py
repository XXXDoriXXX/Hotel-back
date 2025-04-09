from datetime import datetime

from pydantic import BaseModel, EmailStr
from typing import Optional
class ProfileUpdateRequest(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[EmailStr]
    phone: Optional[str]
    birth_date: Optional[datetime]

    class Config:
        from_attributes = True
class ChangeCredentialsRequest(BaseModel):
    current_password: str
    confirm_password: str
    new_password: Optional[str] = None
    new_email: Optional[EmailStr] = None
class AvatarRequest(BaseModel):
    avatar_url: Optional[str]

class PersonBase(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: str
    birth_date: Optional[datetime] = None
    avatar_url: Optional[str] = None
    class Config:
        from_attributes = True