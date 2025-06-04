from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:qwe20236@localhost/hotell_db"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    conn.execute(text("DROP SCHEMA public CASCADE"))
    conn.execute(text("CREATE SCHEMA public"))
    conn.commit()

print("Schema dropped and recreated.")
from models import Base

Base.metadata.create_all(bind=engine)
print("✅ All tables created.")
