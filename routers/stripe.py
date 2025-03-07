import os

from dotenv import load_dotenv

import stripe
from fastapi import APIRouter, HTTPException
from schemas import PaymentRequest, PaymentResponse

router = APIRouter(tags=["Stripe"])
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
        return PaymentResponse(id=intent.id, status=intent.status)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
