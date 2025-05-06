from typing import List
from sqlalchemy import func, case
from starlette.responses import RedirectResponse
import stripe
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, subqueryload
from datetime import datetime
from database import get_db
from models import Room, Owner, Booking, Payment, Client, PaymentError, Hotel, HotelImg, PaymentStatus, BookingStatus
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

    if data.date_start >= data.date_end:
        raise HTTPException(400, detail="End date must be after start date")

    if data.date_start < datetime.utcnow():
        raise HTTPException(400, detail="Cannot book for past dates")

    nights = (data.date_end - data.date_start).days
    if nights < 1:
        raise HTTPException(400, detail="Booking must be at least 1 night")

    overlapping_booking = db.query(Booking).filter(
        Booking.room_id == data.room_id,
        Booking.status.in_(["pending_payment", "awaiting_confirmation", "confirmed"]),
        Booking.date_end > data.date_start,
        Booking.date_start < data.date_end
    ).first()

    if overlapping_booking:
        raise HTTPException(400, detail="Room already booked for selected dates")

    if data.payment_method not in ["cash", "card"]:
        raise HTTPException(400, detail="Invalid payment method")

    total_price = int(room.price_per_night * nights * 100)
    owner = room.hotel.owner

    if not owner.stripe_account_id and data.payment_method == "card":
        raise HTTPException(400, detail="Owner has no Stripe account")

    booking_status = "awaiting_confirmation" if data.payment_method == "cash" else "pending_payment"

    booking = Booking(
        client_id=user["id"],
        room_id=data.room_id,
        date_start=data.date_start,
        date_end=data.date_end,
        status=booking_status
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
            description="Cash payment on arrival"
        ))
        db.commit()
        return {"message": "Booking created, waiting for owner confirmation"}

    else:
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
            success_url=(
                f"{DOMAIN}/bookings/redirect/booking-success?"
                f"booking_id={booking.id}"
                f"&total_price={room.price_per_night * nights:.2f}"
                f"&booking_date={datetime.utcnow().date()}"
            ),

            cancel_url=f"{DOMAIN}/booking/cancel",
            payment_intent_data={
                "application_fee_amount": int(total_price * PLATFORM_FEE_PERCENT),
                "transfer_data": {"destination": owner.stripe_account_id}
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

    if booking.status != BookingStatus.awaiting_confirmation:
        raise HTTPException(400, "Only awaiting confirmation bookings can be confirmed")

    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()

    if not payment or payment.is_card:
        raise HTTPException(400, "Payment is not cash or not found")

    booking.status = BookingStatus.confirmed
    payment.status = PaymentStatus.paid
    payment.paid_at = datetime.utcnow()
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

    if booking.status != BookingStatus.awaiting_confirmation:
        raise HTTPException(400, "Only awaiting confirmation bookings can be cancelled")

    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()

    if not payment or payment.is_card:
        raise HTTPException(400, "Payment is not cash or not found")

    booking.status = BookingStatus.cancelled
    payment.status = PaymentStatus.failed
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
        raise HTTPException(403, "You can only refund your own bookings")

    payment = db.query(Payment).filter(Payment.booking_id == booking_id).first()
    if not payment:
        raise HTTPException(400, "Payment not found")

    if not payment.is_card:
        booking.status = BookingStatus.cancelled
        payment.status = PaymentStatus.failed
        db.commit()
        return {"message": "Cash booking marked as cancelled"}

    now = datetime.utcnow()
    if (booking.date_start - now).total_seconds() < 86400:
        raise HTTPException(400, "Cannot refund within 24 hours of check-in")

    if payment.status != PaymentStatus.paid:
        raise HTTPException(400, "No paid payment found")

    days_left = (booking.date_start - now).days
    refund_pct = min(1.0, days_left / 7.0)
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

    if booking.room.hotel.owner_id != owner.id:
        raise HTTPException(403, "You can refund only your own hotel's bookings")

    payment = db.query(Payment).filter(Payment.booking_id == booking_id, Payment.status == "paid").first()
    if not payment:
        raise HTTPException(400, "No paid payment found")

    if request.amount <= 0 or request.amount > payment.amount:
        raise HTTPException(400, "Refund amount invalid")

    try:
        stripe.Refund.create(
            payment_intent=payment.stripe_payment_id,
            amount=int(request.amount * 100)
        )
        payment.status = "refunded"
        payment.description = f"Manual refund: ${request.amount}"
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
def redirect_to_app(booking_id: int, total_price: float, booking_date: str):
    return RedirectResponse(
        f"myapp://booking/success"
        f"?booking_id={booking_id}"
        f"&total_price={total_price:.2f}"
        f"&booking_date={booking_date}"
    )



@router.get("/my", response_model=List[BookingHistoryItem])
def get_my_bookings(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
    sort_by: str = Query("created_at", regex="^(created_at|status)$"),
    order: str = Query("desc", regex="^(asc|desc)$")
):
    if sort_by == "status":
        sort_column = case(
            (Booking.status == "confirmed", 1),
            (Booking.status == "pending_payment", 2),
            (Booking.status == "awaiting_confirmation", 3),
            (Booking.status == "cancelled", 4),
            else_=5
        )
    else:
        sort_column = Booking.created_at

    order_func = sort_column.asc() if order == "asc" else sort_column.desc()

    bookings = (
        db.query(
            Booking.id.label("booking_id"),
            Booking.room_id,
            Room.room_type,
            Booking.date_start,
            Booking.date_end,
            Hotel.name.label("hotel_name"),
            (Room.price_per_night * func.DATE_PART('day', Booking.date_end - Booking.date_start)).label("total_price"),
            Booking.status,
            Booking.created_at,
            Hotel.id.label("hotel_id")
        )
        .join(Room, Booking.room_id == Room.id)
        .join(Hotel, Room.hotel_id == Hotel.id)
        .filter(
            Booking.client_id == user["id"],
            Booking.is_archived == False
        )
        .order_by(order_func)
        .all()
    )

    result = []
    for booking in bookings:
        hotel_images = db.query(HotelImg).filter(HotelImg.hotel_id == booking.hotel_id).all()
        result.append({
            "booking_id": booking.booking_id,
            "room_id": booking.room_id,
            "room_type": booking.room_type,
            "date_start": booking.date_start,
            "date_end": booking.date_end,
            "hotel_name": booking.hotel_name,
            "total_price": booking.total_price,
            "status": booking.status,
            "created_at": booking.created_at,
            "hotel_images": hotel_images
        })

    return result
@router.delete("/{booking_id}")
def delete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")

    if booking.client_id != user["id"]:
        raise HTTPException(403, "You can delete only your own bookings")

    if booking.status != BookingStatus.cancelled:
        raise HTTPException(400, "Only cancelled bookings can be deleted")

    db.delete(booking)
    db.commit()
    return {"message": "Booking permanently deleted"}
@router.post("/{booking_id}/archive")
def archive_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking not found")

    if booking.client_id != user["id"]:
        raise HTTPException(403, "You can archive only your own bookings")

    if booking.status != BookingStatus.completed:
        raise HTTPException(400, "Only completed bookings can be archived")

    booking.is_archived = True
    db.commit()
    return {"message": "Booking archived"}
