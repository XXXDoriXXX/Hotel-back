from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import Hotel, Owner
from utils import verify_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if "is_owner" not in payload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User role not defined"
        )

    return payload



def get_current_owner(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Owner:
    if not user.get("is_owner"):
        raise HTTPException(
            status_code=403,
            detail="Only owners can perform this action"
        )

    owner = db.query(Owner).filter(Owner.id == user["id"]).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    return owner



def is_hotel_owner(
        hotel_id: int,
        user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> Hotel:

    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    owner = db.query(Owner).filter(Owner.id == hotel.owner_id).first()
    if not owner or owner.person_id != user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this hotel"
        )

    return hotel