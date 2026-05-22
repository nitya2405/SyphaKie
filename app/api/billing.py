"""Stripe billing: credit top-up checkout sessions and webhook handler."""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.credit import Credit
from app.models.credit_transaction import CreditTransaction
from app.models.notification import Notification

router = APIRouter()

# Credit packs: price in USD cents → credits
CREDIT_PACKS = [
    {"id": "pack_500",   "credits": 500,   "price_usd": 500,   "label": "Starter — 500 credits"},
    {"id": "pack_1500",  "credits": 1500,  "price_usd": 1200,  "label": "Growth — 1,500 credits"},
    {"id": "pack_5000",  "credits": 5000,  "price_usd": 3500,  "label": "Pro — 5,000 credits"},
    {"id": "pack_15000", "credits": 15000, "price_usd": 9000,  "label": "Scale — 15,000 credits"},
]


@router.get("/billing/packs")
def list_credit_packs():
    return {"packs": CREDIT_PACKS}


@router.get("/billing/transactions")
def get_transactions(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    txns = (
        db.query(CreditTransaction)
        .filter(CreditTransaction.user_id == current_user.id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(limit)
        .all()
    )
    return {
        "transactions": [
            {
                "id": str(t.id),
                "amount": t.amount,
                "type": t.type,
                "description": t.description,
                "balance_after": t.balance_after,
                "created_at": t.created_at.isoformat(),
            }
            for t in txns
        ]
    }


# ── Auto top-up ───────────────────────────────────────────────────────────────

class AutoTopupRequest(BaseModel):
    threshold: int | None = None   # charge when balance drops below this
    amount: int | None = None      # credits to add (must match a pack)


@router.get("/billing/auto-topup")
def get_auto_topup(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    credit = db.query(Credit).filter_by(user_id=current_user.id).first()
    return {
        "enabled": bool(credit and credit.auto_topup_threshold and credit.auto_topup_amount),
        "threshold": credit.auto_topup_threshold if credit else None,
        "amount": credit.auto_topup_amount if credit else None,
        "has_payment_method": bool(current_user.stripe_payment_method_id),
    }


@router.patch("/billing/auto-topup")
def set_auto_topup(
    body: AutoTopupRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.threshold is not None and body.amount is not None:
        if body.threshold < 0 or body.amount < 0:
            raise HTTPException(status_code=400, detail={"code": "INVALID_VALUES", "message": "Values must be non-negative."})
        if body.amount > 0 and not any(p["credits"] == body.amount for p in CREDIT_PACKS):
            raise HTTPException(status_code=400, detail={"code": "INVALID_AMOUNT", "message": "Amount must match a credit pack size (500, 1500, 5000, or 15000)."})

    credit = db.query(Credit).filter_by(user_id=current_user.id).first()
    if not credit:
        raise HTTPException(status_code=404, detail="Credit record not found.")

    credit.auto_topup_threshold = body.threshold
    credit.auto_topup_amount = body.amount
    db.commit()
    return {
        "enabled": bool(body.threshold and body.amount),
        "threshold": credit.auto_topup_threshold,
        "amount": credit.auto_topup_amount,
    }


async def trigger_auto_topup(db: Session, user: User, balance_after: int) -> bool:
    """Called after credit deduction. Returns True if a top-up was initiated."""
    credit = db.query(Credit).filter_by(user_id=user.id).first()
    if not credit or not credit.auto_topup_threshold or not credit.auto_topup_amount:
        return False
    if balance_after > credit.auto_topup_threshold:
        return False

    pack = next((p for p in CREDIT_PACKS if p["credits"] == credit.auto_topup_amount), None)
    if not pack:
        return False

    # Attempt off-session Stripe charge if payment method is saved
    if user.stripe_payment_method_id:
        try:
            import stripe
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
            if stripe.api_key and user.stripe_customer_id:
                intent = stripe.PaymentIntent.create(
                    amount=pack["price_usd"],
                    currency="usd",
                    customer=user.stripe_customer_id,
                    payment_method=user.stripe_payment_method_id,
                    confirm=True,
                    off_session=True,
                    metadata={"user_id": str(user.id), "credits": str(pack["credits"]), "pack_id": pack["id"], "source": "auto_topup"},
                )
                if intent.status == "succeeded":
                    credit.balance += pack["credits"]
                    db.add(CreditTransaction(
                        id=uuid.uuid4(), user_id=user.id,
                        amount=pack["credits"], type="auto_topup",
                        stripe_payment_intent=intent.id,
                        description=f"Auto top-up: {pack['label']}",
                        balance_after=credit.balance,
                    ))
                    db.add(Notification(
                        id=uuid.uuid4(), user_id=user.id,
                        type="credits_topup",
                        title=f"+{pack['credits']} credits added (auto top-up)",
                        body=f"Your balance dropped below {credit.auto_topup_threshold}. {pack['credits']} credits were added automatically.",
                        link="/account",
                    ))
                    db.commit()
                    return True
        except Exception:
            pass

    # Fallback: send low-balance notification
    db.add(Notification(
        id=uuid.uuid4(), user_id=user.id,
        type="credits_low",
        title="Low credit balance",
        body=f"Your balance is {balance_after} credits — below your auto top-up threshold of {credit.auto_topup_threshold}. Add a payment method to enable automatic top-ups.",
        link="/account",
    ))
    db.commit()
    return False


# ── Checkout ──────────────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    pack_id: str
    success_url: str = "http://localhost:3000/account?topup=success"
    cancel_url: str = "http://localhost:3000/account"


@router.post("/billing/checkout")
def create_checkout_session(
    body: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
        if not stripe.api_key:
            raise HTTPException(status_code=503, detail={"code": "STRIPE_NOT_CONFIGURED", "message": "Stripe is not configured."})
    except ImportError:
        raise HTTPException(status_code=503, detail={"code": "STRIPE_NOT_INSTALLED", "message": "Install stripe: pip install stripe"})

    pack = next((p for p in CREDIT_PACKS if p["id"] == body.pack_id), None)
    if not pack:
        raise HTTPException(status_code=400, detail={"code": "INVALID_PACK", "message": "Unknown credit pack."})

    customer_id = current_user.stripe_customer_id
    if not customer_id:
        customer = stripe.Customer.create(email=current_user.email, name=current_user.name or current_user.email)
        customer_id = customer.id
        current_user.stripe_customer_id = customer_id
        db.commit()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "unit_amount": pack["price_usd"],
                "product_data": {"name": pack["label"]},
            },
            "quantity": 1,
        }],
        mode="payment",
        payment_intent_data={"setup_future_usage": "off_session"},
        success_url=body.success_url,
        cancel_url=body.cancel_url,
        metadata={"user_id": str(current_user.id), "credits": str(pack["credits"]), "pack_id": pack["id"]},
    )

    return {"checkout_url": session.url, "session_id": session.id}


# ── Stripe webhook ────────────────────────────────────────────────────────────

@router.post("/billing/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: Session = Depends(get_db),
):
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    except ImportError:
        raise HTTPException(status_code=503)

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(payload, stripe_signature, webhook_secret)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        meta = session.get("metadata", {})
        user_id = meta.get("user_id")
        credits = int(meta.get("credits", 0))
        pack_id = meta.get("pack_id", "")

        if user_id and credits:
            user = db.query(User).filter_by(id=user_id).first()
            if user:
                # Save payment method for future auto top-up charges
                payment_intent_id = session.get("payment_intent")
                if payment_intent_id and not user.stripe_payment_method_id:
                    try:
                        pi = stripe.PaymentIntent.retrieve(payment_intent_id)
                        pm_id = pi.get("payment_method")
                        if pm_id:
                            user.stripe_payment_method_id = pm_id
                    except Exception:
                        pass

                credit = db.query(Credit).filter_by(user_id=user.id).first()
                if not credit:
                    credit = Credit(id=uuid.uuid4(), user_id=user.id, balance=0)
                    db.add(credit)
                credit.balance += credits
                db.add(CreditTransaction(
                    id=uuid.uuid4(), user_id=user.id,
                    amount=credits, type="topup",
                    stripe_payment_intent=session.get("payment_intent"),
                    description=f"Credit top-up: {pack_id}",
                    balance_after=credit.balance,
                ))
                db.add(Notification(
                    id=uuid.uuid4(), user_id=user.id,
                    type="credits_topup",
                    title=f"+{credits} credits added",
                    body=f"Your purchase of {credits} credits was successful.",
                    link="/account",
                ))
                db.commit()

    return {"received": True}
