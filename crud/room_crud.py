from sqlalchemy.orm import Session
from models import Room, Media, EntityType

def create_room(db: Session, room_data: dict):
    db_room = Room(**room_data)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

def get_rooms(db: Session):
    return db.query(Room).all()

def get_room_by_id(db: Session, room_id: int):
    return db.query(Room).filter(Room.id == room_id).first()

def delete_room(db: Session, room_id: int):
    room = db.query(Room).filter(Room.id == room_id).first()
    if room:
        db.delete(room)
        db.commit()
        return True
    return False

def add_room_media(db: Session, room_id: int, image_url: str):
    room_media = Media(
        entity_type=EntityType.ROOM,
        entity_id=room_id,
        image_url=image_url
    )
    db.add(room_media)
    db.commit()
    db.refresh(room_media)
    return room_media