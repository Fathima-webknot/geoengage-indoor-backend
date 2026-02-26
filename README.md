# GeoEngage Backend

Backend API for GeoEngage Indoor POC. Serves **Android app** (users) and **Web dashboard** (admin).  
Auth: Firebase ID token in `Authorization: Bearer <token>`. DB: Supabase (Postgres). FCM for push notifications.

## Setup

1. **Python 3.11**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   # source .venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt
   ```

2. **Environment**

   Copy `.env.example` to `.env` and set:
   - `DATABASE_URL`: Supabase Postgres connection string
   - `FIREBASE_CREDENTIALS_PATH`: Path to Firebase service account JSON

3. **Database**

   Tables are created on startup via SQLAlchemy `create_all`. Ensure Supabase (Postgres) is reachable and `DATABASE_URL` is set.

4. **Run**

   ```bash
   uvicorn app.main:app --reload
   ```

   - API: http://localhost:8000  
   - Swagger UI: http://localhost:8000/docs  
   - ReDoc: http://localhost:8000/redoc  

## API Overview

| Client   | Endpoints |
|----------|-----------|
| User (Android) | `POST /api/v1/register-device`, `GET /api/v1/me`, `GET /api/v1/zones`, `GET /api/v1/floors`, `POST /api/v1/event`, `GET /api/v1/notifications`, `POST /api/v1/notification-click` |
| Admin (Web)    | `POST /api/v1/campaigns`, `PUT /api/v1/campaigns/{id}`, `GET /api/v1/campaigns`, `GET /api/v1/analytics` |

All protected routes require: `Authorization: Bearer <Firebase_ID_Token>`.

## Rate limiting

Default: 100 requests per minute per IP. Configure via `RATE_LIMIT_PER_MINUTE` in `.env`.

## Tests

Requires a Postgres DB (use `TEST_DATABASE_URL` or same `DATABASE_URL`). Firebase is mocked.

```bash
pytest tests/ -v
```
