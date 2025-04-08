from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import stripe
from database import get_db
from models import Booking, Room, BookingStatus, PaymentMethod, Payment, PaymentStatus
from crud.booking_crud import create_booking, delete_booking
import logging

from schemas import PaymentIntentResponse, BookingCreate, BookingResponse
from schemas.payment import PaymentIntentRequest

router = APIRouter(
    prefix="/bookings",
    tags=["bookings"]
)
logger = logging.getLogger(__name__)
MAX_BOOKING_DAYS = 30
MIN_CHECKIN_HOURS = 24


@router.post("/create-payment-intent", response_model=PaymentIntentResponse)
def create_payment_intent(
        request: PaymentIntentRequest,
        db: Session = Depends(get_db)
):
    validate_booking_dates(request.booking_data)

    if not is_room_available(db, request.booking_data):
        raise HTTPException(
            status_code=400,
            detail="Room not available for selected dates"
        )

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(request.amount * 100),
            currency="usd",
            payment_method_types=["card"],
            metadata={
                "client_id": str(request.booking_data.client_id),
                "room_id": str(request.booking_data.room_id),
                "dates": f"{request.booking_data.date_start} to {request.booking_data.date_end}"
            },
            capture_method="manual"
        )

        db_payment = Payment(
            amount=request.amount,
            status=PaymentStatus.PENDING,
            method=PaymentMethod.CARD,
            stripe_payment_id=intent.id,
            description=f"Booking for room {request.booking_data.room_id}"
        )
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)

        return PaymentIntentResponse(
            payment_intent_id=intent.id,
            client_secret=intent.client_secret,
            status=intent.status
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Payment processing error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@router.post("/confirm-booking", response_model=BookingResponse)
def confirm_booking(
        booking_data: BookingCreate,
        payment_intent_id: Optional[str] = None,
        db: Session = Depends(get_db),
        user_agent: Optional[str] = Header(None)
):
    try:
        validate_booking_dates(booking_data)

        room = db.query(Room).filter(Room.id == booking_data.room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        if not is_room_available(db, booking_data):
            raise HTTPException(
                status_code=400,
                detail="Room not available for selected dates"
            )

        total_days = (booking_data.date_end - booking_data.date_start).days
        total_price = total_days * room.price_per_night

        if booking_data.payment_method == PaymentMethod.CASH:
            return handle_cash_payment(db, booking_data, total_price)
        else:
            return handle_card_payment(
                db, booking_data, total_price, payment_intent_id, user_agent
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Booking confirmation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during booking confirmation"
        )


@router.post("/cancel-booking/{booking_id}")
def cancel_booking(
        booking_id: int,
        db: Session = Depends(get_db)
):

    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        if booking.status not in [BookingStatus.PENDING, BookingStatus.CONFIRMED]:
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel booking in current status"
            )
        if booking.payment and booking.payment.method == PaymentMethod.CARD:
            handle_payment_refund(booking, db)
        booking.status = BookingStatus.CANCELLED
        db.commit()

        return {"message": "Booking cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancellation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error during cancellation"
        )


@router.get("/")
def get_all_bookings(db: Session = Depends(get_db)):
    return db.query(Booking).all()


@router.get("/{booking_id}")
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking
@router.delete("/{booking_id}")
def delete_booking(booking_id: int, db: Session = Depends(get_db)):

    try:
        deleted_booking = delete_booking(db, Booking, booking_id)
        return deleted_booking
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def validate_booking_dates(booking_data: BookingCreate):
    if booking_data.date_start >= booking_data.date_end:
        raise HTTPException(
            status_code=400,
            detail="End date must be after start date"
        )

    if (booking_data.date_end - booking_data.date_start).days > MAX_BOOKING_DAYS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum booking duration is {MAX_BOOKING_DAYS} days"
        )

    min_checkin = datetime.now() + timedelta(hours=MIN_CHECKIN_HOURS)
    if booking_data.date_start < min_checkin.date():
        raise HTTPException(
            status_code=400,
            detail=f"Check-in must be at least {MIN_CHECKIN_HOURS} hours from now"
        )


def is_room_available(db: Session, booking_data: BookingCreate) -> bool:
    conflicting_bookings = db.query(Booking).filter(
        Booking.room_id == booking_data.room_id,
        Booking.date_end > booking_data.date_start,
        Booking.date_start < booking_data.date_end,
        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
    ).count()

    return conflicting_bookings == 0


def handle_cash_payment(db: Session, booking_data: BookingCreate, total_price: float):
    db_payment = Payment(
        amount=total_price,
        status=PaymentStatus.CASH,
        method=PaymentMethod.CASH,
        description=f"Cash booking for room {booking_data.room_id}"
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    db_booking = Booking(
        client_id=booking_data.client_id,
        room_id=booking_data.room_id,
        date_start=booking_data.date_start,
        date_end=booking_data.date_end,
        total_price=total_price,
        payment_id=db_payment.id,
        status=BookingStatus.CONFIRMED
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    return BookingResponse(
        id=db_booking.id,
        status=db_booking.status,
        payment_status=db_payment.status
    )


def handle_card_payment(
        db: Session,
        booking_data: BookingCreate,
        total_price: float,
        payment_intent_id: str,
        user_agent: str
):
    if not payment_intent_id:
        raise HTTPException(
            status_code=400,
            detail="Payment intent ID required for card payments"
        )

    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)

        if abs(intent.amount - int(total_price * 100)) > 100:
            raise HTTPException(
                status_code=400,
                detail="Payment amount doesn't match booking total"
            )

        if intent.status != "succeeded":
            stripe.PaymentIntent.cancel(payment_intent_id)
            raise HTTPException(
                status_code=402,
                detail="Payment not completed",
                headers={"Retry-After": "300"}
            )

        payment = db.query(Payment).filter(
            Payment.stripe_payment_id == payment_intent_id
        ).first()

        if not payment:
            raise HTTPException(
                status_code=400,
                detail="Payment record not found"
            )

        payment.status = PaymentStatus.PAID
        payment.paid_at = datetime.utcnow()
        payment.description = f"Card payment for booking (User-Agent: {user_agent})"

        db_booking = Booking(
            client_id=booking_data.client_id,
            room_id=booking_data.room_id,
            date_start=booking_data.date_start,
            date_end=booking_data.date_end,
            total_price=total_price,
            payment_id=payment.id,
            status=BookingStatus.CONFIRMED
        )

        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)

        return BookingResponse(
            id=db_booking.id,
            status=db_booking.status,
            payment_status=payment.status
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error during confirmation: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Payment verification failed: {str(e)}"
        )


def handle_payment_refund(booking: Booking, db: Session):
    try:
        if booking.payment.status == PaymentStatus.PAID:
            refund = stripe.Refund.create(
                payment_intent=booking.payment.stripe_payment_id,
                reason="requested_by_customer"
            )

            if refund.status == "succeeded":
                booking.payment.status = PaymentStatus.REFUNDED
                db.commit()
            else:
                logger.warning(f"Refund failed for payment {booking.payment.id}")

    except stripe.error.StripeError as e:
        logger.error(f"Refund error: {str(e)}")