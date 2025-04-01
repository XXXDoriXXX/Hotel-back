from sqlalchemy.orm import Session
from models import Hotel, HotelImage

def create_hotel(db: Session, hotel_data: dict):
    db_hotel = Hotel(**hotel_data)
    db.add(db_hotel)
    db.commit()
    db.refresh(db_hotel)
    return db_hotel

def get_hotels(db: Session):
    return db.query(Hotel).all()

def get_hotel_by_id(db: Session, hotel_id: int):
    return db.query(Hotel).filter(Hotel.id == hotel_id).first()

def delete_hotel(db: Session, hotel_id: int):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if hotel:
        db.delete(hotel)
        db.commit()
        return True
    return False

def create_hotel_image(db: Session, hotel_id: int, image_url: str):
    db_image = HotelImage(hotel_id=hotel_id, image_url=image_url)
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image