import os

from fastapi import FastAPI
from database import Base, engine
from routers import owners, clients, hotels, rooms, bookings, auth, people, employees, profile
from fastapi.staticfiles import StaticFiles
from routers import stripe
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(owners.router)
app.include_router(clients.router)
app.include_router(hotels.router)
app.include_router(rooms.router)
app.include_router(bookings.router)
app.include_router(auth.router)
app.include_router(people.router)
app.include_router(profile.router)
app.include_router(employees.router)
app.include_router(stripe.router, prefix="/stripe")

UPLOAD_DIRECTORY = "uploaded_images"
if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)
app.mount("/uploaded_images", StaticFiles(directory=UPLOAD_DIRECTORY), name="uploaded_images")
@app.get("/")
def read_root():
    return {"message": "Welcome to the Hotel Booking API"}
