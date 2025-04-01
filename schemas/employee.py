from typing import Optional

from pydantic import BaseModel, Field
from .person import PersonBase

class EmployeeBase(BaseModel):
    position: str
    salary: float
    work_experience: int
    is_vacation: bool = False

class EmployeeCreate(PersonBase):
    hotel_id: int
    position: str
    salary: float
    work_experience: int
    is_vacation: bool

class Employee(EmployeeBase):
    employee_id: int = Field(alias="id")
    person: PersonBase

    class Config:
        from_attributes = True

class EmployeeDetails(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[str]
    phone: str
    position: str
    salary: float
    work_experience: int
    is_vacation: bool

    class Config:
        from_attributes = True