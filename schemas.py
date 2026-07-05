from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime
from models import UserRole, PaymentStatus, TicketStatus


# ── AUTH ──────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole
    name: str


# ── USER ──────────────────────────────────────────────────────────────────────
class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


# ── LOCKER ────────────────────────────────────────────────────────────────────
class LockerCreate(BaseModel):
    number: str
    zone: str
    monthly_rate: float
    due_date: Optional[date] = None
    notes: Optional[str] = None
    tenant_id: Optional[str] = None

class LockerUpdate(BaseModel):
    zone: Optional[str] = None
    monthly_rate: Optional[float] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None
    tenant_id: Optional[str] = None

class LockerOut(BaseModel):
    id: str
    number: str
    zone: str
    monthly_rate: float
    due_date: Optional[date]
    notes: Optional[str]
    is_occupied: bool
    tenant: Optional[UserOut]
    created_at: datetime

    class Config:
        from_attributes = True


# ── PAYMENT ───────────────────────────────────────────────────────────────────
class PaymentCreate(BaseModel):
    locker_id: str
    amount: float
    due_date: Optional[date] = None

class PaymentOut(BaseModel):
    id: str
    amount: float
    status: PaymentStatus
    due_date: Optional[date]
    paid_at: Optional[datetime]
    created_at: datetime
    locker: Optional[LockerOut]

    class Config:
        from_attributes = True

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


# ── SUPPORT TICKET ────────────────────────────────────────────────────────────
class TicketCreate(BaseModel):
    subject: str
    message: str

class TicketReply(BaseModel):
    admin_reply: str
    status: Optional[TicketStatus] = TicketStatus.in_progress

class TicketOut(BaseModel):
    id: str
    subject: str
    message: str
    status: TicketStatus
    admin_reply: Optional[str]
    customer: Optional[UserOut]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
