# Order Management API

![Status](https://img.shields.io/badge/status-complete-brightgreen)

A production-style e-commerce backend API — product catalog, promotions, cart, and order management — built with Django REST Framework, PostgreSQL, Celery, and Redis.

## Features

- **Custom User Model** — set up from project init, following Django best practices
- **JWT Authentication** — register, login, token refresh, and logout (with refresh token blacklisting) via `djangorestframework-simplejwt`; session authentication also enabled for the browsable API
- **Product & Category catalog** — full CRUD, with category shown by name (not ID) via `SlugRelatedField`
- **Promotions** — many-to-many discounts on products, with automatic "best discount wins" price calculation
- **Cart system** — supports both anonymous (UUID-keyed) and authenticated carts; adding an existing product merges quantity instead of duplicating; live-computed subtotals and cart total
- **Checkout** — converts a cart into a real order inside an atomic database transaction; each order item stores a *frozen* price at time of purchase, so historical orders don't change if product prices change later
- **Async order confirmation emails** — sent via Celery, triggered automatically on successful checkout, without blocking the API response
- **Redis caching** — product list responses are cached to reduce database load
- **Pagination** — all list endpoints are paginated
- **Fully tested** — 31 automated tests covering auth, cart logic, checkout (including a transaction-rollback test), promotions, and the async email task
- **Dockerized** — Django, PostgreSQL, Redis, and a dedicated Celery worker all run together via Docker Compose, production-ready with gunicorn and whitenoise

## Tech Stack

- **Backend:** Python, Django, Django REST Framework
- **Database:** PostgreSQL
- **Auth:** JWT (djangorestframework-simplejwt) + Session Authentication
- **Async tasks:** Celery
- **Broker / Cache:** Redis
- **Containerization:** Docker, Docker Compose
- **Production server:** Gunicorn
- **Static files:** Whitenoise

## Getting Started

### Prerequisites
- Docker and Docker Compose installed

### Setup

1. Clone the repository
   ```bash
   git clone https://github.com/soburwebdevs/order-management-api.git
   cd order-management-api
   ```

2. Create a `.env` file in the project root (see `.env.example` for the required variables)

3. Build and run with Docker Compose
   ```bash
   docker-compose up --build
   ```

4. In a separate terminal, run migrations and create a superuser
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

5. Visit `http://localhost:8000/store/products/` to browse the API, or `http://localhost:8000/admin/` for the admin panel

## API Endpoints

| Method | Endpoint | Description | Auth required |
|--------|----------|--------------|----------------|
| POST | `/account/register/` | Register a new user | No |
| POST | `/account/login/` | Log in, receive JWT access + refresh tokens | No |
| POST | `/account/token/refresh/` | Get a new access token | No |
| POST | `/account/logout/` | Log out (blacklists the refresh token) | Yes |
| GET | `/store/categories/` | List categories | No |
| GET | `/store/products/` | List products (paginated, cached) | No |
| GET | `/store/products/<id>/` | Retrieve a product, with computed discounted price | No |
| POST | `/store/carts/` | Create a cart | No |
| GET | `/store/carts/<uuid>/` | View a cart and its items | No |
| POST | `/store/carts/<uuid>/items/` | Add an item to a cart | No |
| PATCH | `/store/carts/<uuid>/items/<id>/` | Update a cart item's quantity | No |
| DELETE | `/store/carts/<uuid>/items/<id>/` | Remove a cart item | No |
| POST | `/store/orders/` | Checkout — convert a cart into an order | Yes |

## Running Tests

```bash
docker-compose exec web python manage.py test
```

## What I Learned

Building this project meant solving problems beyond standard CRUD: designing a cart system that supports both anonymous and authenticated users, wrapping checkout in a database transaction so a partial failure can never leave orders or carts in a broken state, and freezing historical prices on orders so they stay accurate even after a product's price changes. The biggest jump was introducing Celery and Redis for genuine reasons — asynchronous order confirmation emails and response caching — rather than as resume keywords, including running a dedicated Celery worker container alongside the web server in Docker Compose, and correctly scoping test-only settings (like `CELERY_TASK_ALWAYS_EAGER`) so tests stay fast and isolated without changing real runtime behavior.