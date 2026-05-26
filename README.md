# TeamsBoard

A Django REST API for a multi-tenant Knowledge Base (KB) service. Companies register, receive an API key and JWT, query the shared KB, and admins can view aggregated usage analytics.

## Tech Stack

- Python / Django 5.2
- Django REST Framework + SimpleJWT
- PostgreSQL 16 (via Docker Compose)
- `python-dotenv` for configuration

## Project Structure

```
TeamsBoard/
├── api/                 # KB app: models, views, serializers, permissions, signals
│   ├── models.py        # Company, KBEntry, QueryLog
│   ├── views.py         # Register, Login, KBQuery, UsageSummary
│   ├── serializers.py
│   ├── permissions.py   # IsAdminUser
│   ├── signals.py       # Auto-create Company + api_key on User creation
│   └── urls.py
├── teamboard/           # Django project settings
├── docker-compose.yml   # Postgres service
├── manage.py
├── requirements.txt
└── TeamsBoard.json      # Postman collection
```

## Data Model

- **Company** — one-to-one with `User`. Holds `company_name`, unique `api_key`, and `role` (`admin` / `client`). Created automatically via signal when a User registers.
- **KBEntry** — `question`, `answer`, and `category` (`api`, `database`, `cloud`, `framework`, `general`).
- **QueryLog** — records every KB query (`company`, `search_term`, `results_count`, `queried_at`).

## Setup

### 1. Clone and install

```bash
git clone https://github.com/Kushal859/TeamsBoard.git
cd TeamsBoard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment

Create a `.env` file in the project root:

```env
SECRET_KEY=replace-me
DEBUG=True

POSTGRES_DB=teamsboard
POSTGRES_USER=teamsboard
POSTGRES_PASSWORD=teamsboard
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### 3. Start Postgres

```bash
docker compose up -d
```

### 4. Migrate and run

```bash
python manage.py migrate
python manage.py runserver
```

The API is now available at `http://localhost:8000/`.

## API Endpoints

All endpoints are prefixed per the project's root URL configuration. Authenticated endpoints require a `Authorization: Bearer <access_token>` header.

| Method | Path                          | Auth     | Description                            |
| ------ | ----------------------------- | -------- | -------------------------------------- |
| POST   | `/auth/register/`             | Public   | Register a user + company, returns JWT |
| POST   | `/auth/login/`                | Public   | Log in, returns JWT                    |
| POST   | `/kb/query/`                  | JWT      | Search KB; logs every query            |
| GET    | `/admin/usage-summary/`       | JWT (admin) | Aggregated usage analytics          |

### Register

```http
POST /auth/register/
{
  "username": "acme",
  "password": "supersecret",
  "email": "owner@acme.io",
  "company_name": "Acme Inc."
}
```

Response includes `access` (JWT) and the auto-generated `api_key`.

### KB Query

```http
POST /kb/query/
Authorization: Bearer <access>
{ "search": "postgres" }
```

Performs a case-insensitive match on `question` and `answer`, and writes a `QueryLog` row.

### Admin Usage Summary

```http
GET /admin/usage-summary/
Authorization: Bearer <admin-access>
```

Returns `total_queries`, `active_companies`, and the top 5 `search_term`s.

A Postman collection (`TeamsBoard.json`) is included for quick testing.

## Notes

- A signal in `api/signals.py` creates the `Company` row and assigns a unique `api_key` automatically when a `User` is created.
- `IsAdminUser` (in `api/permissions.py`) checks `request.user.company.role == 'admin'`.
- JWT access tokens are valid for 1 hour (see `SIMPLE_JWT` in `teamboard/settings.py`).
