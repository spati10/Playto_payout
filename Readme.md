# Playto Payout Engine

A minimal payout engine built for the Playto Founding Engineer Challenge 2026. The system lets merchants view balances, request payouts to verified bank accounts, and track payout lifecycle transitions while enforcing money integrity, idempotency, and concurrency safety.[1][2]

## Features

- Merchant dashboard for available balance, held balance, payout history, and payout creation.
- Payout request API with `Idempotency-Key` support.
- Concurrency-safe balance hold using database transactions and row locking.
- Background payout processor with legal state transitions only.
- Retry handling for payouts stuck in `processing` for more than 30 seconds, with exponential backoff and a maximum of 3 attempts.
- Atomic refund of held funds when a payout fails.
- Seed data for demo merchants, balances, and bank accounts.
- Docker Compose support for local development.

## Stack

- Backend: Django + Django REST Framework
- Database: PostgreSQL
- Background jobs: Celery
- Frontend: React + Tailwind CSS
- Containerization: Docker Compose

## Payout lifecycle

Legal transitions are:

- `pending -> processing -> completed`
- `pending -> processing -> failed`

Illegal transitions are rejected centrally in the payout service layer. Failed payouts return held funds atomically in the same database transaction as the state change.[1][2]

## Local setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. Configure environment

Create a `.env` file for backend and frontend values.

Example backend env:

```env
POSTGRES_DB=playto
POSTGRES_USER=playto
POSTGRES_PASSWORD=playto
POSTGRES_HOST=db
POSTGRES_PORT=5432
DJANGO_SETTINGS_MODULE=config.settings
SECRET_KEY=change-me
DEBUG=1
```

Example frontend env:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## Run with Docker

```bash
docker compose up --build
```

If PostgreSQL credentials were changed after the first container start, recreate the DB volume so Postgres reinitializes with the current password values.[1]

```bash
docker compose down -v
docker compose up --build
```

## Apply migrations

```bash
docker compose exec backend python manage.py migrate
```

## Seed demo data

```bash
docker compose exec backend python manage.py seed_data
```

## Run tests

```bash
docker compose exec backend python manage.py test
```

The expected minimum test coverage for this challenge includes:

- one concurrency test proving two simultaneous payout requests cannot both overdraw the same balance
- one idempotency test proving the same `Idempotency-Key` returns the same logical result instead of creating duplicate payouts

## API overview

### Create payout

`POST /api/v1/payouts/`

Headers:

```http
Idempotency-Key: <uuid>
Content-Type: application/json
```

Body:

```json
{
  "merchant_id": "<merchant-uuid>",
  "bank_account_id": "<bank-account-uuid>",
  "amount_paise": 1000
}
```

### Get payout

`GET /api/v1/payouts/<payout_id>/`

## Implementation notes

### Concurrency safety

Balance reservation is handled inside a database transaction using `select_for_update()` on the merchant balance row. This prevents two concurrent requests from reading the same available balance and both succeeding.[2][3]

### Idempotency

Idempotency keys are scoped per merchant and persisted server-side. A duplicate request with the same key returns the original response instead of creating a second payout.[4]

### Retry policy

If a payout remains in `processing` for more than 30 seconds, it is retried with exponential backoff. After 3 attempts, it is marked `failed` and funds are returned atomically.[5][6]

## Suggested project structure

```text
backend/
  apps/
    idempotency/
    ledger/
    merchants/
    payouts/
  config/
frontend/
  src/
    api/
    components/
```

## Deployment

The app can be deployed on Railway, Render, Fly.io, or Koyeb. Seed the deployment with test data before submitting so the reviewer can immediately verify balances, payout creation, and payout history.[4]