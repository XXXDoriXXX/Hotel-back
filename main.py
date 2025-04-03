import os
from fastapi import FastAPI
from database import Base, engine
from routers import (
    owners, clients, hotels, rooms,
    bookings, auth, people, employees,
    profile, stripe
)
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Hotel Booking API",
    description="API для системи бронювання готелів",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

routers = [
    owners.router,
    clients.router,
    hotels.router,
    rooms.router,
    bookings.router,
    auth.router,
    people.router,
    profile.router,
    stripe.router,
    employees.router
]

for router in routers:
    app.include_router(router)

UPLOAD_DIRECTORY = "uploaded_images"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOAD_DIRECTORY), name="static")

@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "Welcome to the Hotel Booking API",
        "docs": "/docs",
        "redoc": "/redoc"
    }