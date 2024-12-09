from fastapi import FastAPI
from database import Base, engine
from routers import owners, clients, hotels, rooms, bookings

# Створення таблиць
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Підключення роутерів
app.include_router(owners.router)
app.include_router(clients.router)
app.include_router(hotels.router)
app.include_router(rooms.router)
app.include_router(bookings.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Hotel Booking API"}
