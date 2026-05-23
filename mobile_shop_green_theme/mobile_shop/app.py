from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'mobileshop_secret_key_2024'

DB = 'shop.db'

# ─── DB HELPERS ───────────────────────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'customer',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            category TEXT,
            image_url TEXT DEFAULT '/static/images/default.png',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            total REAL NOT NULL,
            payment_method TEXT DEFAULT 'cod',
            status TEXT DEFAULT 'Pending',
            address TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER,
            price REAL,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        );
    ''')
    # Seed admin
    try:
        db.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                   ('Admin', 'admin@shop.com', generate_password_hash('admin123'), 'admin'))
    except:
        pass
    # Seed products
    products = [
        ('iPhone 15 Pro Case', 'Premium leather case with MagSafe', 1299, 50, 'Cases', '/static/images/case1.png'),
        ('Samsung S24 Screen Guard', 'Tempered glass 9H hardness', 499, 100, 'Screen Guards', '/static/images/screen1.png'),
        ('Type-C Fast Charger 65W', 'GaN charger with dual ports', 1899, 30, 'Chargers', '/static/images/charger1.png'),
        ('Wireless Earbuds TWS', 'Active noise cancellation earbuds', 3499, 25, 'Audio', '/static/images/earbuds1.png'),
        ('Magnetic Car Mount', '360° rotation wireless charging mount', 999, 60, 'Mounts', '/static/images/mount1.png'),
        ('USB-C Hub 7-in-1', 'HDMI, SD card, USB ports hub', 2199, 20, 'Accessories', '/static/images/hub1.png'),
        ('Pop Socket Grip', 'Expandable grip & stand', 299, 150, 'Grips', '/static/images/pop1.png'),
        ('Powerbank 20000mAh', 'Fast charging slim powerbank', 2799, 35, 'Power', '/static/images/pb1.png'),
    ]
    for p in products:
        try:
            db.execute("INSERT INTO products (name, description, price, stock, category, image_url) VALUES (?,?,?,?,?,?)", p)
        except:
            pass
    db.commit()
    db.close()

# ─── AUTH DECORATORS ──────────────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access only.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated

# ─── AUTH ROUTES ──────────────────────────────────────────────────────────────

@app.route('/')
def home():
    return redirect(url_for('customer_home'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        db.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('customer_home'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        db = get_db()
        try:
            db.execute("INSERT INTO users (name, email, password) VALUES (?,?,?)", (name, email, password))
            db.commit()
            flash('Account created! Please login.', 'success')
            return redirect(url_for('login'))
        except:
            flash('Email already registered.', 'danger')
        finally:
            db.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─── CUSTOMER ROUTES ──────────────────────────────────────────────────────────

@app.route('/shop')
def customer_home():
    db = get_db()
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    query = "SELECT * FROM products WHERE stock > 0"
    params = []
    if category:
        query += " AND category=?"; params.append(category)
    if search:
        query += " AND name LIKE ?"; params.append(f'%{search}%')
    products = db.execute(query, params).fetchall()
    categories = db.execute("SELECT DISTINCT category FROM products").fetchall()
    cart_count = 0
    if session.get('user_id'):
        cart_count = db.execute("SELECT SUM(quantity) FROM cart WHERE user_id=?", (session['user_id'],)).fetchone()[0] or 0
    db.close()
    return render_template('customer/home.html', products=products, categories=categories,
                           cart_count=cart_count, selected_category=category, search=search)

@app.route('/product/<int:pid>')
def product_detail(pid):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    db.close()
    return render_template('customer/product_detail.html', product=product)

@app.route('/cart/add/<int:pid>', methods=['POST'])
@login_required
def add_to_cart(pid):
    qty = int(request.form.get('quantity', 1))
    db = get_db()
    existing = db.execute("SELECT * FROM cart WHERE user_id=? AND product_id=?",
                          (session['user_id'], pid)).fetchone()
    if existing:
        db.execute("UPDATE cart SET quantity=quantity+? WHERE id=?", (qty, existing['id']))
    else:
        db.execute("INSERT INTO cart (user_id, product_id, quantity) VALUES (?,?,?)",
                   (session['user_id'], pid, qty))
    db.commit(); db.close()
    flash('Added to cart!', 'success')
    return redirect(url_for('customer_home'))

@app.route('/cart')
@login_required
def cart():
    db = get_db()
    items = db.execute('''SELECT c.id, c.quantity, p.name, p.price, p.image_url, p.id as pid
                          FROM cart c JOIN products p ON c.product_id=p.id
                          WHERE c.user_id=?''', (session['user_id'],)).fetchall()
    total = sum(i['price'] * i['quantity'] for i in items)
    db.close()
    return render_template('customer/cart.html', items=items, total=total)

@app.route('/cart/remove/<int:cid>')
@login_required
def remove_cart(cid):
    db = get_db()
    db.execute("DELETE FROM cart WHERE id=? AND user_id=?", (cid, session['user_id']))
    db.commit(); db.close()
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    db = get_db()
    items = db.execute('''SELECT c.id, c.quantity, p.name, p.price, p.id as pid
                          FROM cart c JOIN products p ON c.product_id=p.id
                          WHERE c.user_id=?''', (session['user_id'],)).fetchall()
    total = sum(i['price'] * i['quantity'] for i in items)
    if request.method == 'POST':
        address = request.form['address']
        payment = request.form['payment']
        order = db.execute("INSERT INTO orders (user_id, total, payment_method, address) VALUES (?,?,?,?)",
                           (session['user_id'], total, payment, address))
        oid = order.lastrowid
        for item in items:
            db.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?,?,?,?)",
                       (oid, item['pid'], item['quantity'], item['price']))
            db.execute("UPDATE products SET stock=stock-? WHERE id=?", (item['quantity'], item['pid']))
        db.execute("DELETE FROM cart WHERE user_id=?", (session['user_id'],))
        db.commit(); db.close()
        flash('Order placed successfully! 🎉', 'success')
        return redirect(url_for('my_orders'))
    db.close()
    return render_template('customer/checkout.html', items=items, total=total)

@app.route('/my-orders')
@login_required
def my_orders():
    db = get_db()
    orders = db.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC",
                        (session['user_id'],)).fetchall()
    order_details = []
    for o in orders:
        items = db.execute('''SELECT oi.quantity, oi.price, p.name FROM order_items oi
                              JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?''', (o['id'],)).fetchall()
        order_details.append({'order': o, 'items': items})
    db.close()
    return render_template('customer/orders.html', order_details=order_details)

# ─── ADMIN ROUTES ─────────────────────────────────────────────────────────────

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    db = get_db()
    stats = {
        'total_products': db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        'total_orders': db.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        'total_customers': db.execute("SELECT COUNT(*) FROM users WHERE role='customer'").fetchone()[0],
        'total_revenue': db.execute("SELECT SUM(total) FROM orders WHERE status!='Cancelled'").fetchone()[0] or 0,
        'pending_orders': db.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'").fetchone()[0],
    }
    recent_orders = db.execute('''SELECT o.*, u.name as customer_name FROM orders o
                                  JOIN users u ON o.user_id=u.id ORDER BY o.created_at DESC LIMIT 5''').fetchall()
    db.close()
    return render_template('admin/dashboard.html', stats=stats, recent_orders=recent_orders)

@app.route('/admin/products')
@login_required
@admin_required
def admin_products():
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
    db.close()
    return render_template('admin/products.html', products=products)

@app.route('/admin/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    if request.method == 'POST':
        db = get_db()
        db.execute("INSERT INTO products (name, description, price, stock, category, image_url) VALUES (?,?,?,?,?,?)",
                   (request.form['name'], request.form['description'], float(request.form['price']),
                    int(request.form['stock']), request.form['category'], request.form.get('image_url', '/static/images/default.png')))
        db.commit(); db.close()
        flash('Product added!', 'success')
        return redirect(url_for('admin_products'))
    return render_template('admin/product_form.html', product=None)

@app.route('/admin/products/edit/<int:pid>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(pid):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if request.method == 'POST':
        db.execute("UPDATE products SET name=?, description=?, price=?, stock=?, category=?, image_url=? WHERE id=?",
                   (request.form['name'], request.form['description'], float(request.form['price']),
                    int(request.form['stock']), request.form['category'],
                    request.form.get('image_url', product['image_url']), pid))
        db.commit(); db.close()
        flash('Product updated!', 'success')
        return redirect(url_for('admin_products'))
    db.close()
    return render_template('admin/product_form.html', product=product)

@app.route('/admin/products/delete/<int:pid>')
@login_required
@admin_required
def delete_product(pid):
    db = get_db()
    db.execute("DELETE FROM products WHERE id=?", (pid,))
    db.commit(); db.close()
    flash('Product deleted.', 'info')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@login_required
@admin_required
def admin_orders():
    db = get_db()
    orders = db.execute('''SELECT o.*, u.name as customer_name, u.email FROM orders o
                           JOIN users u ON o.user_id=u.id ORDER BY o.created_at DESC''').fetchall()
    order_details = []
    for o in orders:
        items = db.execute('''SELECT oi.quantity, oi.price, p.name FROM order_items oi
                              JOIN products p ON oi.product_id=p.id WHERE oi.order_id=?''', (o['id'],)).fetchall()
        order_details.append({'order': o, 'items': items})
    db.close()
    return render_template('admin/orders.html', order_details=order_details)

@app.route('/admin/orders/update/<int:oid>', methods=['POST'])
@login_required
@admin_required
def update_order_status(oid):
    db = get_db()
    db.execute("UPDATE orders SET status=? WHERE id=?", (request.form['status'], oid))
    db.commit(); db.close()
    flash('Order status updated!', 'success')
    return redirect(url_for('admin_orders'))

@app.route('/admin/customers')
@login_required
@admin_required
def admin_customers():
    db = get_db()
    customers = db.execute('''SELECT u.*, COUNT(o.id) as order_count, SUM(o.total) as total_spent
                              FROM users u LEFT JOIN orders o ON u.id=o.user_id
                              WHERE u.role='customer' GROUP BY u.id''').fetchall()
    db.close()
    return render_template('admin/customers.html', customers=customers)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
