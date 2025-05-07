from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_owner
from models import Employee, Hotel, SalaryHistory
from schemas.employee import EmployeeCreate, EmployeeBase, EmployeeUpdate, SalaryHistoryBase

router = APIRouter(prefix="/employees", tags=["employees"])
MAX_EMPLOYEES_PER_HOTEL = 50

@router.post("/", response_model=EmployeeBase)
def add_employee(emp: EmployeeCreate, db: Session = Depends(get_db), owner=Depends(get_current_owner)):
    hotel = db.query(Hotel).filter_by(id=emp.hotel_id, owner_id=owner.id).first()
    if not hotel:
        raise HTTPException(403, "Not your hotel")
    count = db.query(Employee).filter_by(hotel_id=emp.hotel_id).count()
    if count >= MAX_EMPLOYEES_PER_HOTEL:
        raise HTTPException(400, "Max employee limit reached")
    e = Employee(**emp.dict())
    db.add(e)
    db.commit()
    db.refresh(e)
    return e

@router.put("/{id}")
def update_employee(id: int, update: EmployeeUpdate, db: Session = Depends(get_db), owner=Depends(get_current_owner)):
    emp = db.query(Employee).get(id)
    if not emp or emp.hotel.owner_id != owner.id:
        raise HTTPException(403, "Forbidden")
    if update.salary and update.salary != emp.salary:
        db.add(SalaryHistory(
            employee_id=emp.id,
            old_salary=emp.salary,
            new_salary=update.salary
        ))
        emp.salary = update.salary
    if update.position:
        emp.position = update.position
    if update.hotel_id and update.hotel_id != emp.hotel_id:
        new_hotel = db.query(Hotel).filter_by(id=update.hotel_id, owner_id=owner.id).first()
        if not new_hotel:
            raise HTTPException(400, "Invalid hotel")
        emp.hotel_id = update.hotel_id
    db.commit()
    db.refresh(emp)
    return emp

@router.delete("/{id}")
def fire_employee(id: int, db: Session = Depends(get_db), owner=Depends(get_current_owner)):
    emp = db.query(Employee).get(id)
    if not emp or emp.hotel.owner_id != owner.id:
        raise HTTPException(403, "Not yours")
    db.delete(emp)
    db.commit()
    return {"detail": "Deleted"}

@router.get("/", response_model=List[EmployeeBase])
def get_all_employees(db: Session = Depends(get_db), owner=Depends(get_current_owner)):
    return db.query(Employee).join(Hotel).filter(Hotel.owner_id == owner.id).all()

@router.get("/hotel/{hotel_id}", response_model=List[EmployeeBase])
def get_by_hotel(hotel_id: int, db: Session = Depends(get_db), owner=Depends(get_current_owner)):
    hotel = db.query(Hotel).filter_by(id=hotel_id, owner_id=owner.id).first()
    if not hotel:
        raise HTTPException(403)
    return db.query(Employee).filter_by(hotel_id=hotel_id).all()

@router.get("/{id}/salary-history", response_model=List[SalaryHistoryBase])
def get_salary_log(id: int, db: Session = Depends(get_db), owner=Depends(get_current_owner)):
    emp = db.query(Employee).get(id)
    if not emp or emp.hotel.owner_id != owner.id:
        raise HTTPException(403)
    return db.query(SalaryHistory).filter_by(employee_id=id).order_by(SalaryHistory.changed_at.desc()).all()
