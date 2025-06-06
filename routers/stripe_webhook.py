import stripe
import os
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Booking, Payment, PaymentError, BookingStatus, PaymentStatus
from datetime import datetime

router = APIRouter(prefix="/stripe", tags=["stripe"])
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        booking_id = metadata.get("booking_id")

        if not booking_id:
            return {"status": "ok, no booking_id in metadata"}

        booking = db.query(Booking).filter(Booking.id == int(booking_id)).first()
        if not booking:
            return {"status": "ok, booking not found"}

        if booking.status != BookingStatus.pending_payment:
            return {"status": "ok, booking is not pending payment"}

        payment = db.query(Payment).filter(Payment.booking_id == booking.id, Payment.is_card == True).first()

        if not payment:
            return {"status": "ok, payment not found"}

        booking.status = BookingStatus.confirmed
        payment.status = PaymentStatus.paid
        payment.stripe_payment_id = session["payment_intent"]
        payment.paid_at = datetime.utcnow()

        db.commit()
        return {"status": "success"}

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        metadata = intent.get("metadata", {})
        booking_id = metadata.get("booking_id")

        if booking_id:
            payment = db.query(Payment).join(Booking).filter(Booking.id == int(booking_id)).first()
            if payment:
                db.add(PaymentError(
                    payment_id=payment.id,
                    error_code="payment_failed",
                    error_message="Payment failed via Stripe"
                ))
                payment.status = PaymentStatus.failed
                db.commit()

        return {"status": "fail logged"}

    return {"status": "ignored"}
