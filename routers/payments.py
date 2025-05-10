import stripe
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_owner, get_current_user
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
@router.get("/status")
def get_stripe_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = db.query(Owner).filter(Owner.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.stripe_account_id:
        return {"connected": False}

    try:
        acct = stripe.Account.retrieve(user.stripe_account_id)
        return {"connected": acct.charges_enabled}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
