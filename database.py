from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL вашої бази даних (PostgreSQL у вашому випадку)
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:qwe20236@localhost/hotel_booking"

# Створення двигуна SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Сесія для роботи з базою даних
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовий клас для моделей
Base = declarative_base()

# Функція для отримання сесії бази даних
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
