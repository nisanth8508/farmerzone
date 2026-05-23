# 📱 MobiZone – Mobile Accessories E-Commerce (Flask)

## Project Structure
```
mobile_shop/
├── app.py                  # Main Flask app
├── requirements.txt        # Dependencies
├── shop.db                 # SQLite database (auto-created)
└── templates/
    ├── base.html           # Shared base layout
    ├── login.html          # Login page
    ├── register.html       # Register page
    ├── customer/
    │   ├── home.html       # Shop / product listing
    │   ├── cart.html       # Shopping cart
    │   ├── checkout.html   # Checkout with COD/UPI/Card
    │   └── orders.html     # Customer order history
    └── admin/
        ├── dashboard.html  # Admin stats & recent orders
        ├── products.html   # Product list
        ├── product_form.html  # Add/Edit product form
        ├── orders.html     # All orders + status update
        └── customers.html  # Customer list
```

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
python app.py
```

### 3. Open in browser
```
http://127.0.0.1:5000
```

## Default Admin Login
- **Email:** admin@shop.com
- **Password:** admin123

## Features

### Customer Panel
- Register / Login
- Browse mobile accessories by category
- Search products
- Add to cart, update quantities
- Checkout with Cash on Delivery / UPI / Card
- View order history & status

### Admin Panel
- Dashboard with stats (revenue, orders, customers)
- Product Management: Add, Edit, Delete products
- Order Management: View all orders, update status (Pending → Processing → Shipped → Delivered)
- Customer list with order counts and spending

## Product Categories
Cases | Screen Guards | Chargers | Audio | Mounts | Accessories | Grips | Power

## Tech Stack
- **Backend:** Python Flask
- **Database:** SQLite (via sqlite3)
- **Auth:** Werkzeug password hashing + Flask sessions
- **Frontend:** Pure HTML/CSS (no extra dependencies)
