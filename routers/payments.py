from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas import BookingCreate
from models import Booking, Room
import stripe
import crud

router = APIRouter(
    prefix="/payments",
    tags=["payments"]
)

stripe.api_key = "sk_test_51QvkR6GEyS0IOVdozmQT8g5SaNfABA2br7vFUVVFXwLDL5eXrrWCtSQGHONGAED7OWYIESPj8zKYgJDC5Jh9OsAX00izhXPVoG"

@router.post("/")
def process_payment(payment_data: dict, db: Session = Depends(get_db)):
    try:
        charge = stripe.PaymentIntent.create(
            amount=int(payment_data["total_price"] * 100),
            currency="usd",
            payment_method_data={
                "type": "card",
                "card": {
                    "token": payment_data["token"]
                }
            },
            confirm=True
        )

        if charge["status"] == "succeeded":
            booking_data = BookingCreate(
                client_id=payment_data["user_id"],
                room_id=payment_data["room_id"],
                date_start=payment_data["check_in"],
                date_end=payment_data["check_out"],
                total_price=payment_data["total_price"]
            )
            db_booking = crud.create_booking(db, booking_data.dict())
            return {"status": "success", "booking_id": db_booking.id}
        else:
            raise HTTPException(status_code=400, detail="Payment failed")

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
