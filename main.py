from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from database import engine
import models
from routers import auth, admin, customer, payments


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    models.Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="LockerBase API",
    description="Locker management system with Stripe payments",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — update origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your Railway domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(customer.router)
app.include_router(payments.router)

# Serve frontend files
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")


@app.get("/")
def root():
    return {
        "status": "LockerBase API running",
        "employee_portal": "/frontend/employee.html",
        "customer_portal": "/frontend/customer.html",
        "docs": "/docs",
    }


# ── Seed an admin user on first run ──────────────────────────────────────────
@app.on_event("startup")
def seed_admin():
    from database import SessionLocal
    from auth import hash_password

    db = SessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@lockerbase.com")
        admin_pass  = os.getenv("ADMIN_PASSWORD", "changeme123")

        existing = db.query(models.User).filter(models.User.email == admin_email).first()
        if not existing:
            admin_user = models.User(
                email=admin_email,
                name="Admin",
                hashed_password=hash_password(admin_pass),
                role=models.UserRole.admin,
            )
            db.add(admin_user)
            db.commit()
            print(f"[LockerBase] Admin created: {admin_email}")
    finally:
        db.close()
