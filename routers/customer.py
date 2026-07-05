from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models, schemas
from auth import get_current_user

router = APIRouter(prefix="/customer", tags=["customer"])


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.get("/locker", response_model=schemas.LockerOut)
def get_my_locker(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    locker = db.query(models.Locker).filter(models.Locker.tenant_id == current_user.id).first()
    if not locker:
        raise HTTPException(status_code=404, detail="No locker assigned to your account")
    return locker


@router.get("/payments", response_model=List[schemas.PaymentOut])
def get_my_payments(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Payment)\
             .filter(models.Payment.customer_id == current_user.id)\
             .order_by(models.Payment.created_at.desc())\
             .all()


@router.post("/tickets", response_model=schemas.TicketOut)
def submit_ticket(body: schemas.TicketCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    ticket = models.SupportTicket(
        customer_id=current_user.id,
        subject=body.subject,
        message=body.message,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/tickets", response_model=List[schemas.TicketOut])
def get_my_tickets(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.SupportTicket)\
             .filter(models.SupportTicket.customer_id == current_user.id)\
             .order_by(models.SupportTicket.created_at.desc())\
             .all()
