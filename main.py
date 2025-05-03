import os
from datetime import datetime

from fastapi import FastAPI
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from database import Base, engine
from routers import (
    auth, hotels, rooms, profile, amenities, stripe_webhook, payments, bookings, favorite
)
from fastapi.middleware.cors import CORSMiddleware

from tasks import auto_complete_bookings
from apscheduler.schedulers.background import BackgroundScheduler

app = FastAPI(
    title="Hotel Booking API",
    description="API для системи бронювання готелів",
    version="1.0.0"
)
app.add_middleware(ProxyHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # локальний фронт
        "https://hotel-back-production-558e.up.railway.app"  # деплой
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)

routers = [
    auth.router,
    hotels.router,
    rooms.router,
    profile.router,
    amenities.router,
    stripe_webhook.router,
    payments.router,
    bookings.router,
    favorite.router

]

for router in routers:
    app.include_router(router)
scheduler = BackgroundScheduler()
scheduler.add_job(
    auto_complete_bookings,
    trigger="interval",
    hours=12,
    next_run_time=datetime.utcnow()
)
scheduler.start()
@app.get("/", tags=["Root"])
async def read_root():
    return {
        "message": "Welcome to the Hotel Booking API",
        "docs": "/docs",
        "redoc": "/redoc"
    }