# 🛒 E-Commerce API

**A comprehensive, scalable RESTful API for building modern e-commerce platforms**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.1.6-green.svg)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/Django%20REST%20Framework-3.15.2-brightgreen.svg)](https://www.django-rest-framework.org/)

---

## 🚀 Overview

The **E-Commerce API** is a powerful, feature-rich backend solution for building modern e-commerce platforms. Built with Django and Django REST Framework, this API provides all the essential components for a complete online store: product management, user authentication, shopping carts, wishlists, reviews, orders, and payment processing with Stripe integration.

### Key Features

✅ **User Management** – Custom user model with customer/business roles
✅ **Product Catalog** – CRUD operations with categories, images, and stock management
✅ **Shopping Cart** – Persistent carts with item management
✅ **Wishlist** – Save products for later purchase
✅ **Reviews & Ratings** – Auto-updating product ratings
✅ **Order Processing** – Stripe integration for secure payments
✅ **Address Management** – Customer shipping and billing addresses
✅ **Search & Filtering** – Advanced product search capabilities
✅ **Authentication** – JWT-based authentication with refresh tokens

Perfect for developers building **B2C e-commerce platforms**, **marketplaces**, or **headless commerce solutions**.

---

## 🛠️ Tech Stack

| Category       | Technologies Used                          |
|----------------|--------------------------------------------|
| **Language**   | Python 3.8+                                |
| **Framework**  | Django 5.1.6                              |
| **API**        | Django REST Framework 3.15.2              |
| **Database**   | PostgreSQL (via psycopg2)                 |
| **Authentication** | JWT (JSON Web Tokens)                   |
| **Payments**   | Stripe API                                 |
| **Media**      | Pillow (Image processing)                 |
| **Deployment** | Gunicorn + ASGI (for production)         |
| **Testing**    | Django Test Framework                     |

---

## 📦 Installation

### Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.8+
- PostgreSQL (or SQLite for development)
- Docker (optional, for containerized deployment)
- Git

### Quick Start

1. **Clone the repository:**

```bash
git clone https://github.com/yourusername/ecommerce-api.git
cd ecommerce-api
```

2. **Create and activate a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Set up environment variables:**

Create a `.env` file in the project root with the following variables:

```env
# Database
DATABASE_URL=postgres://username:password@localhost:5432/ecommerce_db

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True

# Stripe
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-webhook-secret

# JWT
SIMPLE_JWT={
    "ACCESS_TOKEN_LIFETIME": "15 minutes",
    "REFRESH_TOKEN_LIFETIME": "1 days",
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}
```

5. **Run migrations:**

```bash
python manage.py migrate
```

6. **Load dump data:**

```bash
python manage.py loaddata data.json
```

7. **Create a superuser (for admin access):**

```bash
python manage.py createsuperuser
```

8. **Start the development server:**

```bash
python manage.py runserver
```

Your API will be available at `http://localhost:8000/api/`.

---

## 🎯 Usage

### Authentication

The API uses JWT for authentication. Here's how to obtain a token:

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "yourpassword"}'
```

**Response:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Use the `access` token in the `Authorization` header for authenticated requests:
```
Authorization: Bearer <your-access-token>
```

---

### Product Management (Business Users Only)

**Create a product:**

```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-access-token>" \
  -d '{
    "name": "Wireless Headphones",
    "description": "Noise-cancelling wireless headphones",
    "price": 199.99,
    "category": 1,
    "stock": 50
  }'
```

**List all products:**

```bash
curl http://localhost:8000/api/products/?category=1
```

---

### Shopping Cart

**Add a product to cart:**

```bash
curl -X POST http://localhost:8000/api/carts/items/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-access-token>" \
  -d '{
    "product": 1,
    "quantity": 2
  }'
```

**Get cart details:**

```bash
curl http://localhost:8000/api/carts/me/ \
  -H "Authorization: Bearer <your-access-token>"
```

---

### Stripe Checkout

**Create a Stripe checkout session:**

```bash
curl -X POST http://localhost:8000/api/orders/checkout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <your-access-token>" \
  -d '{
    "items": [
      {"product_id": 1, "quantity": 2},
      {"product_id": 3, "quantity": 1}
    ]
  }'
```

**Response:**
```json
{
  "session_id": "cs_test_a1b2c3d4e5f6",
  "url": "https://checkout.stripe.com/c/payment/..."
}
```

---

## 📁 Project Structure

```
ecommerce-api/
├── EcoAPI/                  # Django project settings
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── api/                     # Core application
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations/          # Database migrations
│   ├── models.py            # Database models
│   ├── serializers.py       # Serializers
│   ├── tests.py             # Tests
│   ├── urls.py              # API endpoints
│   └── views.py             # View logic
├── manage.py                # Django management script
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

---

## 🔧 Configuration

### Environment Variables

| Variable                     | Description                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| `SECRET_KEY`                 | Django secret key                                                           |
| `DEBUG`                      | Set to `True` for development, `False` for production                        |
| `DATABASE_URL`               | Database connection URL (PostgreSQL recommended)                            |
| `STRIPE_SECRET_KEY`          | Stripe API secret key                                                        |
| `STRIPE_WEBHOOK_SECRET`      | Stripe webhook secret for payment verification                               |
| `ALLOWED_HOSTS`              | Comma-separated list of allowed hosts for production                          |

### Customization Options

1. **User Roles:**
   - Customize user types in `api/models.py` by modifying `USER_TYPE_CHOICES`.

2. **Categories:**
   - Add default categories via Django admin or through the API.

3. **Payment Gateways:**
   - Replace Stripe integration with PayPal or other providers by modifying `api/views.py`.

---
