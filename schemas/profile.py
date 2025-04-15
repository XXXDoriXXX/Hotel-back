from datetime import datetime

from pydantic import BaseModel, EmailStr, Field
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
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[datetime] = None

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
class OwnerUpdateRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    current_password: str = Field(..., min_length=6)
    new_password: str | None = Field(None, min_length=6)
class UpdateOwnerResponse(BaseModel):
    owner: PersonBase
    new_token: str