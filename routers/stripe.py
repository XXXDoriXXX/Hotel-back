import os
from datetime import datetime

from dotenv import load_dotenv
from requests import Session

import crud
import stripe
from fastapi import APIRouter, HTTPException, Depends

from database import get_db
from schemas import PaymentRequest, PaymentResponse, PaymentSuccessRequest

router = APIRouter(
    prefix="/stripe",
    tags=["stripe"]
)
load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@router.post("/create-payment-intent", response_model=PaymentResponse)
def create_payment_intent(payment_request: PaymentRequest):
    try:
        amount_in_cents = int(payment_request.amount * 100)
        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency="usd",
            payment_method_types=["card"],
        )
        return PaymentResponse(
            id=intent.id,
            clientSecret=intent.client_secret,
            status=intent.status
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/payment-success")
def payment_success(request: PaymentSuccessRequest, db: Session = Depends(get_db)):

    payment_data = {
        "amount": request.amount,
        "status": "completed",
        "paid_at": datetime.utcnow()
    }
    db_payment = crud.create_payment(db, payment_data)

    booking_data = {
        "client_id": request.client_id,
        "room_id": request.room_id,
        "date_start": request.date_start,
        "date_end": request.date_end,
        "total_price": request.total_price,
        "payment_id": db_payment.id,
        "status": "completed",
        "paid_at": datetime.utcnow()
    }
    db_booking = crud.create_booking(db, booking_data)

    return {
        "message": "Payment successful and booking created",
        "booking_id": db_booking.id,
        "payment_db_id": db_payment.id
    }