from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas import EmployeeCreate, Employee  # Використовуємо Pydantic схему Employee
from database import get_db
from dependencies import get_current_user
from models import Employee as EmployeeModel  # SQLAlchemy модель
import crud

router = APIRouter(
    prefix="/employees",
    tags=["employees"]
)

@router.post("/", response_model=Employee)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_owner"):
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        new_employee = crud.create_employee(db, employee.dict())
        return new_employee
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating employee: {str(e)}")


@router.delete("/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_owner"):
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        return crud.delete_employee(db, employee_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", response_model=List[Employee])
def get_all_employees(db: Session = Depends(get_db)):
    employees = db.query(EmployeeModel).all()  # Використання SQLAlchemy моделі
    return employees
