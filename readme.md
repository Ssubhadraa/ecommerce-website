# ShopHub — Flask E-Commerce Website

A full-featured e-commerce storefront built with Flask, SQLAlchemy, and SQLite. Includes product catalog, shopping cart, checkout, order management, product recommendations, and an admin panel.

## Tech Stack

- Python Flask
- SQLAlchemy + Flask-Migrate
- Flask-Login + bcrypt
- SQLite
- Jinja2 templates with responsive HTML/CSS/JS

## Quick Start

```bash
cd ecommerce-website
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
flask db upgrade
python seed_products.py
flask run
```

If you already had the database before wishlist was added, run `flask db upgrade` again to create the `wishlist_items` table.

Open http://127.0.0.1:5000

## Default Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@shop.com | admin123 |
| Customer | customer1@example.com | password123 |

## Features

- **Auth** — Register, login, profile, address CRUD
- **Catalog** — Categories, search, filters, sort, pagination, product detail with gallery
- **Cart** — Add/update/remove with stock checks, header badge, toast notifications
- **Wishlist** — Save products, view wishlist page, toggle from product detail and cards
- **Checkout** — Address selection, server-side totals, COD orders, stock decrement
- **Recommendations** — Trending, collaborative filtering, category affinity, cold-start fallback
- **Admin** — Dashboard KPIs, product CRUD with image upload, categories, order management

## Configuration

Environment variables (see `.env.example`):

- `SHIPPING_FLAT_RATE` — Flat shipping fee (default: 50)
- `FREE_SHIPPING_THRESHOLD` — Free shipping above this subtotal (default: 999)
- `TAX_RATE` — Tax rate as decimal (default: 0.18)

## Project Structure

```
app/
├── models/       # SQLAlchemy models
├── routes/       # Blueprints (auth, products, cart, orders, admin)
├── services/     # Business logic (checkout, inventory, recommendations)
├── templates/    # Jinja2 HTML templates
└── static/       # CSS, JS, images
uploads/products/ # Uploaded product images
seed_products.py  # Database seeder
```

## Demo Flow

1. Browse homepage recommendations and categories
2. Search/filter products and view product details
3. Register or login, add items to cart
4. Add a shipping address and checkout (COD)
5. View order history and confirmation
6. Login as admin to manage products and orders
