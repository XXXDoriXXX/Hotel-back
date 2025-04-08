import os
from fastapi import FastAPI
from database import Base, engine
from routers import (
auth, hotels, rooms
)
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
    auth.router,
    hotels.router,
    rooms.router
]

for router in routers:
    app.include_router(router)

@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "Welcome to the Hotel Booking API",
        "docs": "/docs",
        "redoc": "/redoc"
    }