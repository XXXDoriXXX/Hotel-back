from sqlalchemy.orm import Session
from models import Owner, Client
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(Client).filter(Client.email == email).first()
    is_owner = False

    if not user:
        user = db.query(Owner).filter(Owner.email == email).first()
        is_owner = True

    if not user or not verify_password(password, user.password):
        return None

    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "is_owner": is_owner,
        "birth_date": getattr(user, "birth_date", None),
        "owner_id": user.id if is_owner else None
    }


def create_owner(db: Session, data: dict) -> Owner:
    if db.query(Owner).filter((Owner.email == data["email"]) | (Owner.phone == data["phone"])).first():
        raise ValueError("Owner with this email or phone already exists.")

    owner = Owner(
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data["email"],
        phone=data["phone"],
        password=get_password_hash(data["password"])
    )
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return owner


def create_client(db: Session, data: dict) -> Client:
    if db.query(Client).filter((Client.email == data["email"]) | (Client.phone == data["phone"])).first():
        raise ValueError("Client with this email or phone already exists.")

    client = Client(
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data["email"],
        phone=data["phone"],
        password=get_password_hash(data["password"]),
        birth_date=data["birth_date"]
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client
