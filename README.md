# LockerBase

Full-stack locker management system with Stripe payments.

## Stack
- **Backend:** FastAPI + PostgreSQL + SQLAlchemy
- **Auth:** JWT tokens
- **Payments:** Stripe Checkout
- **Hosting:** Railway

---

## Deploy to Railway (Step by Step)

### 1. Push to GitHub
```bash
cd locker-system
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/locker-system.git
git push -u origin main
```

### 2. Create Railway Project
1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Select your `locker-system` repo
3. Railway will auto-detect Python and use `railway.toml`

### 3. Add PostgreSQL
1. In your Railway project → **+ New** → **Database** → **PostgreSQL**
2. Railway will automatically set `DATABASE_URL` in your environment

### 4. Set Environment Variables
In Railway → your service → **Variables**, add:

| Variable | Value |
|---|---|
| `JWT_SECRET` | Run `python -c "import secrets; print(secrets.token_hex(32))"` |
| `STRIPE_SECRET_KEY` | From [Stripe Dashboard](https://dashboard.stripe.com/apikeys) → Secret key |
| `STRIPE_WEBHOOK_SECRET` | See step 5 below |
| `FRONTEND_URL` | Your Railway public URL (e.g. `https://locker-system.up.railway.app`) |
| `ADMIN_EMAIL` | Your admin login email |
| `ADMIN_PASSWORD` | Your admin password |

### 5. Set Up Stripe Webhook
1. Go to [Stripe Dashboard](https://dashboard.stripe.com/webhooks) → Add endpoint
2. URL: `https://your-app.railway.app/payments/webhook`
3. Select event: `checkout.session.completed`
4. Copy the **Signing secret** → set as `STRIPE_WEBHOOK_SECRET`

### 6. Deploy
Railway auto-deploys on every git push. Check logs in the Railway dashboard.

---

## Portals

After deploy:
- **Employee portal:** `https://your-app.railway.app/frontend/employee.html`
- **Customer portal:** `https://your-app.railway.app/frontend/customer.html`
- **API docs:** `https://your-app.railway.app/docs`

---

## First Login

The app auto-creates an admin account on startup using `ADMIN_EMAIL` and `ADMIN_PASSWORD`.

**Workflow:**
1. Log into the employee portal
2. Go to **Customers** → Add Customer (creates their login)
3. Go to **Lockers** → Add Locker → assign the customer
4. Go to **Payments** → Create Payment (sets the amount due)
5. Customer logs into the customer portal and pays via Stripe

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
cp .env.example .env

# Run
uvicorn main:app --reload
```

Then open `http://localhost:8000/frontend/employee.html`

For Stripe webhooks locally, use the [Stripe CLI](https://stripe.com/docs/stripe-cli):
```bash
stripe listen --forward-to localhost:8000/payments/webhook
```
