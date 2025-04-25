import stripe
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_owner
from models import Owner

router = APIRouter(prefix="/payments", tags=["payments"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
DOMAIN = os.getenv("STRIPE_DOMAIN", "http://localhost:5173")

@router.post("/connect")
def create_stripe_account_link(db: Session = Depends(get_db), owner: Owner = Depends(get_current_owner)):
    if not owner.stripe_account_id:
        account = stripe.Account.create(type="standard", email=owner.email)
        owner.stripe_account_id = account.id
        db.commit()

    account_link = stripe.AccountLink.create(
        account=owner.stripe_account_id,
        refresh_url=f"{DOMAIN}/stripe/refresh",
        return_url=f"{DOMAIN}/stripe/return",
        type="account_onboarding",
    )
    return {"url": account_link.url}
