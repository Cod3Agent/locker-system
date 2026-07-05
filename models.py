from sqlalchemy import Column, String, Float, Date, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid
from database import Base


def gen_id():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    admin = "admin"
    customer = "customer"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    overdue = "overdue"


class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"


class User(Base):
    __tablename__ = "users"

    id           = Column(String, primary_key=True, default=gen_id)
    email        = Column(String, unique=True, nullable=False, index=True)
    name         = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role         = Column(Enum(UserRole), default=UserRole.customer)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    locker       = relationship("Locker", back_populates="tenant", uselist=False)
    tickets      = relationship("SupportTicket", back_populates="customer")
    payments     = relationship("Payment", back_populates="customer")


class Locker(Base):
    __tablename__ = "lockers"

    id           = Column(String, primary_key=True, default=gen_id)
    number       = Column(String, unique=True, nullable=False)
    zone         = Column(String, nullable=False)
    monthly_rate = Column(Float, nullable=False)
    due_date     = Column(Date, nullable=True)
    notes        = Column(Text, nullable=True)
    is_occupied  = Column(Boolean, default=False)
    tenant_id    = Column(String, ForeignKey("users.id"), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    tenant       = relationship("User", back_populates="locker")
    payments     = relationship("Payment", back_populates="locker")


class Payment(Base):
    __tablename__ = "payments"

    id                  = Column(String, primary_key=True, default=gen_id)
    customer_id         = Column(String, ForeignKey("users.id"), nullable=False)
    locker_id           = Column(String, ForeignKey("lockers.id"), nullable=False)
    amount              = Column(Float, nullable=False)
    status              = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    stripe_session_id   = Column(String, nullable=True)
    stripe_payment_intent = Column(String, nullable=True)
    due_date            = Column(Date, nullable=True)
    paid_at             = Column(DateTime(timezone=True), nullable=True)
    created_at          = Column(DateTime(timezone=True), server_default=func.now())

    customer            = relationship("User", back_populates="payments")
    locker              = relationship("Locker", back_populates="payments")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id           = Column(String, primary_key=True, default=gen_id)
    customer_id  = Column(String, ForeignKey("users.id"), nullable=False)
    subject      = Column(String, nullable=False)
    message      = Column(Text, nullable=False)
    status       = Column(Enum(TicketStatus), default=TicketStatus.open)
    admin_reply  = Column(Text, nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    customer     = relationship("User", back_populates="tickets")
