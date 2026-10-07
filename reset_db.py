import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("DROP SCHEMA public CASCADE"))
    conn.execute(text("CREATE SCHEMA public"))
    conn.commit()

print("Schema dropped and recreated.")
from models import Base

Base.metadata.create_all(bind=engine)
print("✅ All tables created.")
