# Inventory Management System — Flask Web App

A full-stack web application built with **Flask** for managing products, tracking stock levels, and recording restock and sales orders — with image uploads via **Supabase Storage** and a **PostgreSQL** database.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Setup & Installation](#setup--installation)
- [Pages & Routes](#-pages--routes)
- [Database Schema](#-database-schema)
- [Error Handling](#-error-handling)

---

## Features

- **Authentication** — Seller signup and login with Flask session management
- **Products** — Create, view, update, and soft-delete products with optional image upload
- **Orders** — Create multi-item orders of two types:
  - **Restock (Incoming)** — Increases product stock quantities
  - **Sell (Outgoing)** — Decreases product stock quantities with stock validation
- **Dashboard** — Displays top 5 best-selling products based on outgoing order history
- **Image Uploads** — Product images uploaded to Supabase Storage and served via public URL

---

## Tech Stack

- **Language:** Python
- **Framework:** Flask
- **ORM:** Flask-SQLAlchemy
- **Database:** PostgreSQL (hosted on Supabase)
- **Migrations:** Flask-Migrate (Alembic)
- **File Storage:** Supabase Storage
- **Frontend:** Jinja2 templates + CSS

---

## Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/Dhyey17/InventorySystem.git
cd InventorySystem
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
# PostgreSQL transaction pooler connection (Supabase → Settings → Database)
DB_USER=yuour_supabase_user
DB_PASSWORD=your_db_password
DB_HOST=your_supabase_host
DB_PORT=6543
DB_NAME=postgres

# Flask session secret key (any random string)
SECRETE_KEY=your_secret_key_here

# Supabase API (Supabase → Settings → API)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Optional: enable debug mode
FLASK_DEBUG=1
```

> **Note:** A Supabase account is required. Create a storage bucket named `product-images` and set it to **public**.

### 5. Run database migrations

```bash
flask db upgrade
```

### 6. Start the development server

```bash
python app.py
```

The app will be live at `http://127.0.0.1:5000/`

---

## 🔐 Authentication

This app uses **Flask session-based authentication**. On login, the seller's ID is stored in the session and checked on every protected route using the `login_required()` utility.

Unauthenticated access to protected routes raises an `UnauthorizedError` and redirects the user to the login page.

---

## 📡 Pages & Routes

### 👤 Sellers

| Method   | Route      | Auth Required | Description                        |
|----------|------------|---------------|------------------------------------|
| GET      | `/`        | ❌             | Home page                          |
| GET/POST | `/signup`  | ❌             | Register a new seller              |
| GET/POST | `/login`   | ❌             | Login and start session            |
| GET      | `/logout`  | ✅             | Clear session and redirect to home |

---

### 📦 Products

| Method   | Route                   | Auth Required | Description                  |
|----------|-------------------------|---------------|------------------------------|
| GET      | `/products`             | ✅             | List all products for seller |
| GET/POST | `/products/add`         | ✅             | Add a new product            |
| GET      | `/product/<id>`         | ✅             | View product details         |
| GET/POST | `/products/update/<id>` | ✅             | Edit a product               |
| GET/POST | `/products/delete/<id>` | ✅             | Soft-delete a product        |

**Add / Update Product — form fields:**

| Field      | Type   | Required | Notes                        |
|------------|--------|----------|------------------------------|
| `name`     | text   | ✅        |                              |
| `price`    | number | ✅        | Decimals allowed             |
| `quantity` | number | ✅        | Must be 0 or greater         |
| `category` | text   | ✅        |                              |
| `expiry`   | date   | ❌        | Format: `YYYY-MM-DD`         |
| `image`    | file   | ❌        | Uploaded to Supabase Storage |

---

### 🛒 Orders

| Method | Route                | Auth Required | Description                         |
|--------|----------------------|---------------|-------------------------------------|
| GET    | `/orders`            | ✅             | List all orders for seller          |
| GET    | `/order/create`      | ✅             | View order cart                     |
| POST   | `/order/add-item`    | ✅             | Add a product to the session cart   |
| POST   | `/order/remove-item` | ✅             | Remove an item from the cart        |
| POST   | `/order/submit`      | ✅             | Finalise the order and update stock |
| GET    | `/order/<id>`        | ✅             | View a specific order's details     |

**Submit Order — form fields:**

| Field        | Values                   | Notes                                              |
|--------------|--------------------------|----------------------------------------------------|
| `order_type` | `Incoming` or `Outgoing` | Incoming restocks; Outgoing sells and checks stock |

> **Note:** The order cart is stored in the Flask session. Items persist until the order is submitted or the session expires.

---

### 📊 Dashboard

| Method | Route        | Auth Required | Description                                                |
|--------|--------------|---------------|------------------------------------------------------------|
| GET    | `/dashboard` | ✅             | Top 5 best-selling products (by count of outgoing orders) |

---

## 🗃️ Database Schema

### Sellers

| Column      | Type       | Notes                                         |
|-------------|------------|-----------------------------------------------|
| `ID`        | Integer    | Primary Key                                   |
| `name`      | String(30) | Required                                      |
| `username`  | String(50) | Required, Unique                              |
| `password`  | String(50) | Required                                      |
| `email`     | String(50) | Optional                                      |
| `is_active` | Boolean    | Default `True`; used to soft-disable accounts |

### Products

| Column       | Type        | Notes                             |
|--------------|-------------|-----------------------------------|
| `ID`         | Integer     | Primary Key                       |
| `seller_id`  | Integer     | FK → Sellers                      |
| `name`       | String(100) | Required                          |
| `price`      | Float       | Required                          |
| `quantity`   | Integer     | Required                          |
| `expiry`     | DateTime    | Nullable                          |
| `category`   | String(50)  | Required                          |
| `is_deleted` | Boolean     | Default `False`; soft delete flag |
| `image_url`  | String(500) | Nullable; Supabase public URL     |

### Orders

| Column        | Type       | Notes                         |
|---------------|------------|-------------------------------|
| `ID`          | Integer    | Primary Key                   |
| `seller_id`   | Integer    | FK → Sellers                  |
| `type`        | String(50) | `Incoming` or `Outgoing`      |
| `total_price` | Float      | Auto-calculated at submission |
| `created_at`  | DateTime   | Auto-set to UTC now           |

### OrderItems

| Column       | Type    | Notes                           |
|--------------|---------|---------------------------------|
| `ID`         | Integer | Primary Key                     |
| `order_id`   | Integer | FK → Orders                     |
| `product_id` | Integer | FK → Products                   |
| `quantity`   | Integer | Required                        |
| `price`      | Float   | Snapshot of price at order time |

---

## 🛠️ Error Handling

Custom exception classes are defined in `exceptions.py` and registered as Flask error handlers in `app.py`:

| Exception                | Trigger                                     | Behaviour                                    |
|--------------------------|---------------------------------------------|----------------------------------------------|
| `UnauthorizedError`      | Accessing a protected route without session | Redirects to `/login` with error message     |
| `ItemNotFoundError`      | Product not found or is soft-deleted        | Redirects to `/products` with error message  |
| `InsufficientStockError` | Outgoing order quantity exceeds stock       | Redirects to `/order/create` with error message |

A shared utility `login_required(session)` in `utils.py` raises `UnauthorizedError` when `seller_id` is absent from the session.

---