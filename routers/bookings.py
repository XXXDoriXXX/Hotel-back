from typing import List

from sqlalchemy import func
from starlette.responses import RedirectResponse

import stripe
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, subqueryload
from datetime import datetime
from database import get_db
from models import Room, Owner, Booking, Payment, Client, PaymentError, Hotel, HotelImg
from dependencies import get_current_user, get_current_owner
from schemas.booking import BookingCheckoutRequest, RefundRequest, ManualRefundRequest, BookingHistoryItem

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

    if data.payment_method == "cash":
        db.add(Payment(
            booking_id=booking.id,
            amount=total_price / 100,
            status="pending",
            is_card=False,
            description="Оплата готівкою при заселенні"
        ))
        db.commit()

        return {"message": "Booking created, waiting for owner confirmation"}

    elif data.payment_method == "card":
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
            success_url=f"{DOMAIN}/bookings/redirect/booking-success?booking_id={booking.id}",
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

    else:
        raise HTTPException(400, detail="Invalid payment method")

    return {"checkout_url": session.url}
@router.post("/{booking_id}/confirm-cash")
def confirm_cash_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    owner: Owner = Depends(get_current_owner)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")

    if booking.room.hotel.owner_id != owner.id:
        raise HTTPException(403, "You can confirm only your own hotel's bookings")

    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()

    if not payment or not payment.is_card:
        raise HTTPException(400, "Payment not found or is not cash")

    booking.status = "confirmed"
    db.commit()

    return {"message": "Cash booking confirmed"}
@router.post("/{booking_id}/cancel-cash")
def cancel_cash_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    owner: Owner = Depends(get_current_owner)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")

    if booking.room.hotel.owner_id != owner.id:
        raise HTTPException(403, "You can cancel only your own hotel's bookings")

    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()

    if not payment or not payment.is_card:
        raise HTTPException(400, "Payment not found or is not cash")

    booking.status = "cancelled"
    db.commit()

    return {"message": "Cash booking cancelled"}

@router.post("/{booking_id}/refund-request")
def request_refund(
    booking_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")
    if booking.client_id != user["id"]:
        raise HTTPException(403, "You can only cancel your own bookings")

    now = datetime.utcnow()
    if (booking.date_start - now).total_seconds() < 86400:
        raise HTTPException(400, "You cannot refund within 24 hours of check-in")

    days_left = (booking.date_start - now).days
    refund_pct = min(1.0, days_left / 7.0)
    payment = db.query(Payment).filter(Payment.booking_id == booking_id, Payment.status == "paid").first()

    if not payment:
        raise HTTPException(400, "No valid payment found for refund")

    refund_amount = round(payment.amount * refund_pct, 2)
    refund_cents = int(refund_amount * 100)

    try:
        stripe.Refund.create(
            payment_intent=payment.stripe_payment_id,
            amount=refund_cents
        )
        payment.status = "refunded"
        payment.description = f"Auto refund: {refund_pct * 100:.0f}%"
        booking.status = "cancelled"
        db.commit()
        return {"refunded": refund_amount}
    except Exception as e:
        db.add(PaymentError(
            payment_id=payment.id,
            error_code="refund_failed",
            error_message=str(e)
        ))
        db.commit()
        raise HTTPException(500, "Refund failed")


@router.post("/{booking_id}/refund-manual")
def manual_refund(
    booking_id: int,
    request: ManualRefundRequest,
    db: Session = Depends(get_db),
    owner: Owner = Depends(get_current_owner)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")

    room = booking.room
    hotel = room.hotel

    if hotel.owner_id != owner.id:
        raise HTTPException(403, "You can refund only your own hotel bookings")

    payment = db.query(Payment).filter(Payment.booking_id == booking_id, Payment.status == "paid").first()
    if not payment:
        raise HTTPException(400, "No valid payment found")

    if request.amount > payment.amount:
        raise HTTPException(400, "Refund amount exceeds payment")

    try:
        stripe.Refund.create(
            payment_intent=payment.stripe_payment_id,
            amount=int(request.amount * 100)
        )
        payment.status = "refunded"
        payment.description = f"Manual refund by owner: ${request.amount}"
        db.commit()
        return {"refunded": request.amount}
    except Exception as e:
        db.add(PaymentError(
            payment_id=payment.id,
            error_code="manual_refund_failed",
            error_message=str(e)
        ))
        db.commit()
        raise HTTPException(500, "Manual refund failed")
@router.get("/redirect/booking-success")
def redirect_to_app(booking_id: int):
    return RedirectResponse(f"myapp://booking/success?booking_id={booking_id}")
@router.get("/my", response_model=List[BookingHistoryItem])
def get_my_bookings(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    bookings = (
        db.query(
            Booking.id.label("booking_id"),
            Room.room_type,
            Booking.date_start,
            Booking.date_end,
            Hotel.name.label("hotel_name"),
            (Room.price_per_night * func.DATE_PART('day', Booking.date_end - Booking.date_start)).label("total_price"),
            Booking.status,
            Hotel.id.label("hotel_id")
        )
        .join(Room, Booking.room_id == Room.id)
        .join(Hotel, Room.hotel_id == Hotel.id)
        .filter(Booking.client_id == user["id"])
        .order_by(Booking.created_at.desc())
        .all()
    )

    result = []
    for booking in bookings:
        hotel_images = (
            db.query(HotelImg)
            .filter(HotelImg.hotel_id == booking.hotel_id)
            .all()
        )

        result.append({
            "booking_id": booking.booking_id,
            "room_type": booking.room_type,
            "date_start": booking.date_start,
            "date_end": booking.date_end,
            "hotel_name": booking.hotel_name,
            "total_price": booking.total_price,
            "status": booking.status,
            "hotel_images": hotel_images
        })

    return result
