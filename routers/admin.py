from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from database import get_db
import models, schemas
from auth import require_admin, hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


# ── USERS ─────────────────────────────────────────────────────────────────────
@router.get("/users", response_model=List[schemas.UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(models.User).filter(models.User.role == models.UserRole.customer).all()


@router.post("/users", response_model=schemas.UserOut)
def create_customer(body: schemas.RegisterRequest, db: Session = Depends(get_db), _=Depends(require_admin)):
    existing = db.query(models.User).filter(models.User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = models.User(
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
        role=models.UserRole.customer,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_customer(user_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"detail": "Deleted"}


# ── LOCKERS ───────────────────────────────────────────────────────────────────
@router.get("/lockers", response_model=List[schemas.LockerOut])
def list_lockers(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(models.Locker).all()


@router.post("/lockers", response_model=schemas.LockerOut)
def create_locker(body: schemas.LockerCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    existing = db.query(models.Locker).filter(models.Locker.number == body.number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Locker number already exists")

    locker = models.Locker(**body.model_dump())
    if body.tenant_id:
        locker.is_occupied = True
    db.add(locker)
    db.commit()
    db.refresh(locker)

    # Auto-create first payment when a tenant is assigned
    if body.tenant_id:
        payment = models.Payment(
            customer_id=body.tenant_id,
            locker_id=locker.id,
            amount=body.monthly_rate,
            due_date=body.due_date,
            status=models.PaymentStatus.pending,
        )
        db.add(payment)
        db.commit()

    return locker


@router.put("/lockers/{locker_id}", response_model=schemas.LockerOut)
def update_locker(locker_id: str, body: schemas.LockerUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    locker = db.query(models.Locker).filter(models.Locker.id == locker_id).first()
    if not locker:
        raise HTTPException(status_code=404, detail="Locker not found")

    had_tenant = locker.tenant_id
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(locker, field, value)

    if body.tenant_id:
        locker.is_occupied = True
    elif body.tenant_id == "":
        locker.is_occupied = False
        locker.tenant_id = None

    db.commit()
    db.refresh(locker)

    # Auto-create payment if a new tenant was just assigned
    if body.tenant_id and body.tenant_id != had_tenant:
        payment = models.Payment(
            customer_id=body.tenant_id,
            locker_id=locker.id,
            amount=locker.monthly_rate,
            due_date=locker.due_date,
            status=models.PaymentStatus.pending,
        )
        db.add(payment)
        db.commit()

    return locker


@router.delete("/lockers/{locker_id}")
def delete_locker(locker_id: str, db: Session = Depends(get_db), _=Depends(require_admin)):
    locker = db.query(models.Locker).filter(models.Locker.id == locker_id).first()
    if not locker:
        raise HTTPException(status_code=404, detail="Locker not found")
    db.delete(locker)
    db.commit()
    return {"detail": "Deleted"}


# ── PAYMENTS ──────────────────────────────────────────────────────────────────
@router.get("/payments", response_model=List[schemas.PaymentOut])
def list_payments(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(models.Payment).order_by(models.Payment.created_at.desc()).all()


@router.post("/payments", response_model=schemas.PaymentOut)
def create_payment_record(body: schemas.PaymentCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    locker = db.query(models.Locker).filter(models.Locker.id == body.locker_id).first()
    if not locker or not locker.tenant_id:
        raise HTTPException(status_code=400, detail="Locker not found or has no tenant")

    payment = models.Payment(
        customer_id=locker.tenant_id,
        locker_id=body.locker_id,
        amount=body.amount,
        due_date=body.due_date or locker.due_date,
        status=models.PaymentStatus.pending,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


# ── SUPPORT TICKETS ───────────────────────────────────────────────────────────
@router.get("/tickets", response_model=List[schemas.TicketOut])
def list_tickets(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(models.SupportTicket).order_by(models.SupportTicket.created_at.desc()).all()


@router.put("/tickets/{ticket_id}", response_model=schemas.TicketOut)
def reply_to_ticket(ticket_id: str, body: schemas.TicketReply, db: Session = Depends(get_db), _=Depends(require_admin)):
    ticket = db.query(models.SupportTicket).filter(models.SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.admin_reply = body.admin_reply
    ticket.status = body.status
    db.commit()
    db.refresh(ticket)
    return ticket


# ── DASHBOARD STATS ───────────────────────────────────────────────────────────
@router.get("/stats")
def get_stats(db: Session = Depends(get_db), _=Depends(require_admin)):
    today = date.today()
    total_lockers   = db.query(models.Locker).count()
    occupied        = db.query(models.Locker).filter(models.Locker.is_occupied == True).count()
    overdue         = db.query(models.Locker).filter(
                        models.Locker.due_date < today,
                        models.Locker.is_occupied == True
                      ).count()
    open_tickets    = db.query(models.SupportTicket).filter(
                        models.SupportTicket.status == models.TicketStatus.open
                      ).count()
    paid_this_month = db.query(models.Payment).filter(
                        models.Payment.status == models.PaymentStatus.paid
                      ).count()

    return {
        "total_lockers": total_lockers,
        "occupied": occupied,
        "vacant": total_lockers - occupied,
        "overdue": overdue,
        "open_tickets": open_tickets,
        "paid_this_month": paid_this_month,
    }
