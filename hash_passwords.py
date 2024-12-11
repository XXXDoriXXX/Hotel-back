from sqlalchemy.orm import Session
from models import Person
from crud import get_password_hash
from database import get_db

def hash_all_passwords(db: Session):
    people = db.query(Person).all()
    for person in people:
        if person.password == "default_password":  # Перевірка, щоб не хешувати хешовані паролі
            person.password = get_password_hash(person.password)
    db.commit()
    print("Паролі успішно хешовані.")

if __name__ == "__main__":
    db = next(get_db())
    hash_all_passwords(db)
