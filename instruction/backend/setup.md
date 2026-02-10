# Backend Setup Guide

## Tech Stack

| Component | Version |
|---|---|
| Python | 3.13+ |
| Django | 6.0.2 |
| Django REST Framework | 3.16.1 |
| djangorestframework-simplejwt | 5.5.1 |
| django-cors-headers | 4.9.0 |
| Database | SQLite (default) |

## Project Structure

```
backend/
├── config/                 # Django project package
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py         # Project settings (DRF, JWT, CORS config)
│   ├── urls.py             # Root URL conf with auth endpoints + /me view
│   └── wsgi.py
├── db.sqlite3              # SQLite database (auto-created after migrate)
├── manage.py               # Django management script
├── requirements.txt        # Pip dependencies
└── venv/                   # Python virtual environment
```

## Getting Started

### 1. Create & activate the virtual environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate      # macOS / Linux
# venv\Scripts\activate       # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run migrations

```bash
python manage.py migrate
```

### 4. Create a superuser

```bash
python manage.py createsuperuser
```

### 5. Run the development server

```bash
python manage.py runserver
```

The API is available at `http://127.0.0.1:8000/`.

---

## Authentication (SimpleJWT)

Authentication uses [djangorestframework-simplejwt](https://github.com/jazzband/djangorestframework-simplejwt) with its **default configuration** — no custom serializers or overrides.

### Endpoints

| Method | URL | Description | Auth Required |
|---|---|---|---|
| POST | `/api/auth/token/` | Obtain JWT token pair | No |
| POST | `/api/auth/token/refresh/` | Refresh an access token | No |
| GET | `/api/auth/me/` | Get current user info | Yes (Bearer) |
| — | `/admin/` | Django admin panel | Session |

### Obtain Token Pair

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H 'Content-Type: application/json' \
  -d '{"username": "admin", "password": "admin"}'
```

**Response:**

```json
{
  "access": "eyJhbGciOiJIUzI1...",
  "refresh": "eyJhbGciOiJIUzI1..."
}
```

### Refresh Access Token

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/refresh/ \
  -H 'Content-Type: application/json' \
  -d '{"refresh": "<refresh_token>"}'
```

**Response:**

```json
{
  "access": "eyJhbGciOiJIUzI1..."
}
```

### Get Current User

```bash
curl http://127.0.0.1:8000/api/auth/me/ \
  -H 'Authorization: Bearer <access_token>'
```

**Response:**

```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@example.com",
  "first_name": "",
  "last_name": ""
}
```

---

## Key Configuration

### Django REST Framework (`settings.py`)

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}
```

### SimpleJWT Settings (`settings.py`)

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
}
```

### CORS (`settings.py`)

```python
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]
```

`corsheaders.middleware.CorsMiddleware` is placed **before** `CommonMiddleware` in the `MIDDLEWARE` list.

---

## User Model

Uses Django's **default `auth.User` model** — no custom user model. Users are managed via:

- `python manage.py createsuperuser`
- Django admin panel at `/admin/`

---

## Frontend Integration

The frontend (Vue 3 + Axios) communicates with these endpoints:

| Frontend Action | API Call |
|---|---|
| Login | `POST /api/auth/token/` with `{username, password}` |
| Refresh token | `POST /api/auth/token/refresh/` with `{refresh}` |
| Fetch user | `GET /api/auth/me/` with `Authorization: Bearer <token>` |

The frontend stores the `access` token in localStorage and attaches it to every request via an Axios request interceptor. A response interceptor handles 401 errors by attempting a token refresh before redirecting to login.

---

## References

- [DRF Authentication — JWT](https://www.django-rest-framework.org/api-guide/authentication/#json-web-token-authentication)
- [djangorestframework-simplejwt docs](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Django docs](https://docs.djangoproject.com/en/6.0/)
