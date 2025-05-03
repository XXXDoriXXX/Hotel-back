from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Booking, BookingStatus, PaymentStatus
from database import SessionLocal

def auto_complete_bookings():
    db: Session = SessionLocal()
    now = datetime.utcnow()

    completed = db.query(Booking).filter(
        Booking.status == BookingStatus.confirmed,
        Booking.date_end < now
    ).all()

    for booking in completed:
        booking.status = BookingStatus.completed

    expired_cash = db.query(Booking).filter(
        Booking.status == BookingStatus.awaiting_confirmation,
        Booking.date_start < now.date()
    ).all()

    for booking in expired_cash:
        booking.status = BookingStatus.cancelled
        for p in booking.payments:
            if not p.is_card:
                p.status = PaymentStatus.failed

    if completed or expired_cash:
        print(f"[tasks] Completed: {len(completed)}, Cancelled cash: {len(expired_cash)}")

    db.commit()
    db.close()
def cancel_stale_card_bookings():
    db: Session = SessionLocal()
    now = datetime.utcnow()

    expired = db.query(Booking).filter(
        Booking.status == BookingStatus.pending_payment,
        Booking.created_at < now - timedelta(minutes=10)
    ).all()

    for b in expired:
        b.status = BookingStatus.cancelled
        for p in b.payments:
            if p.is_card:
                p.status = PaymentStatus.failed

    if expired:
        print(f"[tasks] Cancelled stale card bookings: {len(expired)}")

    db.commit()
    db.close()
