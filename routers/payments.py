import os
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
import models, schemas
from auth import get_current_user

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET  = os.getenv("STRIPE_WEBHOOK_SECRET")
FRONTEND_URL    = os.getenv("FRONTEND_URL", "http://localhost:8000")

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/checkout/{payment_id}", response_model=schemas.CheckoutResponse)
def create_checkout_session(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    payment = db.query(models.Payment).filter(
        models.Payment.id == payment_id,
        models.Payment.customer_id == current_user.id,
    ).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status == models.PaymentStatus.paid:
        raise HTTPException(status_code=400, detail="Payment already completed")

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": f"Locker {payment.locker.number} — Monthly Rent",
                    "description": f"Zone: {payment.locker.zone}",
                },
                "unit_amount": int(payment.amount * 100),  # cents
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=f"{FRONTEND_URL}/frontend/customer.html?payment=success",
        cancel_url=f"{FRONTEND_URL}/frontend/customer.html?payment=cancelled",
        metadata={
            "payment_id": payment.id,
            "customer_id": current_user.id,
        },
        customer_email=current_user.email,
    )

    payment.stripe_session_id = session.id
    db.commit()

    return schemas.CheckoutResponse(checkout_url=session.url, session_id=session.id)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session    = event["data"]["object"]
        payment_id = session["metadata"].get("payment_id")

        if payment_id:
            payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
            if payment:
                payment.status                = models.PaymentStatus.paid
                payment.paid_at               = datetime.utcnow()
                payment.stripe_payment_intent = session.get("payment_intent")
                db.commit()

    return JSONResponse({"status": "ok"})
