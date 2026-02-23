# InventorySystem

A Flask-based web application for managing product inventory, tracking stock levels, and recording incoming (restock)
and outgoing (sales) orders — built with PostgreSQL via Supabase and image hosting via Supabase Storage.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Database Schema](#database-schema)
- [Application Routes](#application-routes)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Running Database Migrations](#running-database-migrations)

---

## Features

- **Authentication** — Seller signup, login, logout with session management
- **Products** — Add, view, edit, and soft-delete products with image upload support
- **Orders** — Create multi-item orders of two types:
    - **Restock (Incoming)** — Increases product stock quantities
    - **Sell (Outgoing)** — Decreases product stock quantities with stock validation
- **Dashboard** — Displays the top 5 best-selling products based on outgoing order history
- **Image Uploads** — Product images are uploaded to Supabase Storage and linked via public URL

---

## Tech Stack

- Language: Python
- Backend Framework: Flask
- Frontend: jinja Template and CSS
- Database: PostgreSQL (Supabase)
- ORM: Flask-SQLAlchemy
- Databse Migrations: Flask-Migrate
- File Storage: Supabase Storage (Public Buckets)

---

## Database Schema

### `sellers`

| Column    | Type       | Notes                                         |
|-----------|------------|-----------------------------------------------|
| ID        | Integer    | Primary Key                                   |
| name      | String(30) | Required                                      |
| username  | String(50) | Required, Unique                              |
| password  | String(50) | Required (plain text — see Known Issues)      |
| email     | String(50) | Optional                                      |
| is_active | Boolean    | Default `True`; used for soft account disable |

### `products`

| Column     | Type        | Notes                             |
|------------|-------------|-----------------------------------|
| ID         | Integer     | Primary Key                       |
| seller_id  | Integer     | FK → sellers.ID                   |
| name       | String(100) | Required                          |
| price      | Float       | Required                          |
| quantity   | Integer     | Required                          |
| expiry     | DateTime    | Optional                          |
| category   | String(50)  | Required                          |
| is_deleted | Boolean     | Default `False`; soft delete flag |
| image_url  | String(500) | Optional; Supabase public URL     |

### `orders`

| Column      | Type       | Notes                        |
|-------------|------------|------------------------------|
| ID          | Integer    | Primary Key                  |
| seller_id   | Integer    | FK → sellers.ID              |
| type        | String(50) | `"Incoming"` or `"Outgoing"` |
| total_price | Float      | Computed at order submission |
| created_at  | DateTime   | Auto-set to UTC now          |

### `order_items`

| Column     | Type    | Notes                              |
|------------|---------|------------------------------------|
| ID         | Integer | Primary Key                        |
| order_id   | Integer | FK → orders.ID                     |
| product_id | Integer | FK → products.ID                   |
| quantity   | Integer | Required                           |
| price      | Float   | Snapshot of price at time of order |

---

## Application Routes

| Method   | Route                   | Description                               |
|----------|-------------------------|-------------------------------------------|
| GET      | `/`                     | Home page                                 |
| GET/POST | `/signup`               | Seller registration                       |
| GET/POST | `/login`                | Seller login                              |
| GET      | `/logout`               | Clear session and redirect home           |
| GET      | `/dashboard`            | Top selling products                      |
| GET      | `/products`             | List all products for logged-in seller    |
| GET/POST | `/products/add`         | Add a new product                         |
| GET      | `/product/<id>`         | Product detail view                       |
| GET/POST | `/products/update/<id>` | Edit a product                            |
| GET/POST | `/products/delete/<id>` | Soft-delete a product (confirmation page) |
| GET      | `/orders`               | List all orders for logged-in seller      |
| GET      | `/order/create`         | Create order (cart view)                  |
| POST     | `/order/add-item`       | Add item to session cart                  |
| POST     | `/order/remove-item`    | Remove item from session cart             |
| POST     | `/order/submit`         | Finalise order, update stock              |
| GET      | `/order/<id>`           | Order detail view                         |

---
## Running Database Migrations

This project uses **Flask-Migrate** (Alembic) to manage schema changes.

```bash
# Apply all pending migrations to the database
flask db upgrade

# To create a new migration after changing models.py
flask db migrate -m "describe your change"
flask db upgrade

# To roll back the last migration
flask db downgrade
```