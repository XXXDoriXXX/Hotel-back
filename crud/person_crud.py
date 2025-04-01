from sqlalchemy.orm import Session
from models import Person, Owner, Client
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(db: Session, email: str, password: str):
    person = db.query(Person).filter(Person.email == email).first()
    if not person or not verify_password(password, person.password):
        return None
    owner_id = None
    if person.is_owner:
        owner = db.query(Owner).filter(Owner.person_id == person.id).first()
        owner_id = owner.id if owner else None
    return {
        "id": person.id,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "email": person.email,
        "phone": person.phone,
        "is_owner": person.is_owner,
        "birth_date": person.birth_date,
        "owner_id": owner_id
    }

def create_person(db: Session, person: dict):
    existing_user = db.query(Person).filter(
        (Person.email == person.get("email")) |
        (Person.phone == person.get("phone"))
    ).first()
    if existing_user:
        raise ValueError("User with the same email or phone already exists.")
    hashed_password = get_password_hash(person.get("password"))
    db_person = Person(
        first_name=person.get("first_name"),
        last_name=person.get("last_name"),
        email=person.get("email"),
        phone=person.get("phone"),
        password=hashed_password,
        is_owner=person.get("is_owner", False),
        birth_date=person.get("birth_date")
    )
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person

def create_owner(db: Session, owner_data: dict):
    owner_data["is_owner"] = True
    person = create_person(db, owner_data)
    db_owner = Owner(person_id=person.id)
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)
    return db_owner

def create_client(db: Session, client: dict):
    person = create_person(db, client)
    db_client = Client(person_id=person.id)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client