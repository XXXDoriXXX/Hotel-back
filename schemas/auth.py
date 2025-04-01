from pydantic import BaseModel
from datetime import date
from typing import Optional

class LoginRequest(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ChangeCredentialsRequest(BaseModel):
    current_password: str
    new_password: Optional[str] = None
    new_email: Optional[str] = None