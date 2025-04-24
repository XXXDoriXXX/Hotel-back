import stripe
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from database import get_db
from models import Room, Owner, Booking, Payment, Client
from dependencies import get_current_user
from schemas.booking import BookingCheckoutRequest

router = APIRouter(prefix="/bookings", tags=["bookings"])
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
DOMAIN = os.getenv("STRIPE_DOMAIN", "http://localhost:5173")
PLATFORM_FEE_PERCENT = 0.1  # 10%

@router.post("/checkout")
def create_checkout_session(
    data: BookingCheckoutRequest,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    client = db.query(Client).filter(Client.id == user["id"]).first()
    if not client:
        raise HTTPException(404, detail="Client not found")

    room = db.query(Room).filter(Room.id == data.room_id).first()
    if not room:
        raise HTTPException(404, detail="Room not found")

    nights = (data.date_end - data.date_start).days
    if nights < 1:
        raise HTTPException(400, detail="Invalid date range")

    total_price = int(room.price_per_night * nights * 100)
    owner = room.hotel.owner

    if not owner.stripe_account_id:
        raise HTTPException(400, detail="Owner has no Stripe account")

    # Створення бронювання
    booking = Booking(
        client_id=user["id"],
        room_id=data.room_id,
        date_start=data.date_start,
        date_end=data.date_end,
        status="pending"
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Stripe Checkout
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": f"{room.room_type.value} room"},
                "unit_amount": total_price,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{DOMAIN}/booking/success?booking_id={booking.id}",
        cancel_url=f"{DOMAIN}/booking/cancel",
        payment_intent_data={
            "application_fee_amount": int(total_price * PLATFORM_FEE_PERCENT),
            "transfer_data": {
                "destination": owner.stripe_account_id
            }
        },
        metadata={"booking_id": str(booking.id)}
    )

    db.add(Payment(
        booking_id=booking.id,
        amount=total_price / 100,
        status="pending",
        is_card=True,
        description="Stripe Checkout"
    ))
    db.commit()

    return {"checkout_url": session.url}