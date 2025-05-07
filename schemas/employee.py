from datetime import datetime, date

from typing import Optional

from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    position: str
    salary: float
    hotel_id: int

class EmployeeUpdate(BaseModel):
    position: Optional[str]
    salary: Optional[float]
    hotel_id: Optional[int]

class EmployeeBase(EmployeeCreate):
    id: int
    class Config:
        from_attributes = True

class SalaryHistoryBase(BaseModel):
    employee_id: int
    old_salary: float
    new_salary: float
    changed_at: datetime
    class Config:
        from_attributes = True
