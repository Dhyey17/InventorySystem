import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, session
from flask_migrate import Migrate
from supabase import Client, create_client
from sqlalchemy import func, desc

from exceptions import InsufficientStockError, ItemNotFoundError, UnauthorizedError
from models import db, Sellers, Products, Orders, OrderItems
from utils import login_required

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
PORT = os.getenv("DB_PORT")
DBNAME = os.getenv("DB_NAME")
secret = os.getenv("SECRETE_KEY")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase_url = os.environ.get("SUPABASE_URL")

# Construct the SQLAlchemy connection string
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secret
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG") == "1"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True,
                                           "pool_recycle": 300,
                                           }

db.init_app(app)
migrate = Migrate(app, db)
sb: Client = create_client(supabase_url, supabase_key)


@app.errorhandler(InsufficientStockError)
def insufficient_stock(error):
    return redirect(url_for("create_order", error=str(error)))


@app.errorhandler(ItemNotFoundError)
def item_not_found(error):
    return redirect(url_for("products", error=str(error)))


@app.errorhandler(UnauthorizedError)
def unauthorized(error):
    return redirect(url_for("login", error=str(error)))


@app.route('/')
def home():
    error = request.args.get("error")
    if session.get('seller_id'):
        return redirect(url_for("products"))
    return render_template("home.html", error=error)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = request.args.get("error")
    if request.method == 'POST':
        name = request.form['name'].strip()
        username = request.form['username'].strip()
        password = request.form['password']

        if not name:
            error = 'Name cannot be empty'
        elif not password:
            error = 'Password cannot be empty'
        elif not username:
            error = 'Username cannot be empty'
        elif Sellers.query.filter_by(username=username).first():
            error = 'Username already exists'
        else:
            user = Sellers(username=username, name=name, password=password)
            db.session.add(user)
            db.session.commit()
            session['seller_id'] = user.ID
            return redirect(url_for('products'))
    return render_template('signup.html', error=error)


@app.route("/login", methods=['GET', 'POST'])
def login():
    error = request.args.get("error")
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = Sellers.query.filter_by(username=username, password=password).first()
        if user:
            if user.is_active:
                session['seller_id'] = user.ID
                return redirect(url_for('products'))
            else:
                raise UnauthorizedError("User does not exist")
        else:
            raise UnauthorizedError('Wrong Username and/or Password')
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/dashboard')
def dashboard():
    login_required(session)
    items = (
        db.session.query(
            Products.name.label("name"),
            Products.price.label("Price"),
            func.sum(OrderItems.quantity).label("quantity"),
            func.count(OrderItems.product_id).label("order_count")
        )
        .join(OrderItems, OrderItems.product_id == Products.ID)
        .join(Orders, Orders.ID == OrderItems.order_id)
        .filter(
            Orders.seller_id == session['seller_id'],
            Orders.type == "Outgoing"
        )
        .group_by(Products.ID, Products.name, Products.price)
        .order_by(desc("order_count"))
        .all()
    )

    # Convert result into list of dicts (same format as before)
    result = [
        {
            "name": item.name,
            "Price": item.Price,
            "quantity": item.quantity
        }
        for item in items
    ]

    return render_template("dashboard.html", order_items=result)


@app.route('/products', methods=['GET'])
def products():
    login_required(session)

    status = request.args.get('status')
    error = request.args.get("error")

    products_list = Products.query.filter_by(seller_id=session['seller_id']).all()
    return render_template("products.html", products=products_list, status=status, error=error)


@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    login_required(session)
    error = None
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        price = request.form.get('price', '').strip()
        quantity = request.form.get('quantity', '').strip()
        category = request.form.get('category', '').strip()
        expiry = request.form.get('expiry', '').strip()
        image = request.files.get('image')

        if not name or not price or not quantity or not category:
            error = "All fields except expiry are required"
        else:
            try:
                price_f = float(price)
                quantity_i = int(quantity)
                if price_f < 0 or quantity_i < 0:
                    error = "Price and quantity must be 0 or greater"

                else:
                    if not image and image.filename:
                        image_url = None
                    else:
                        sb.storage.from_("product-images").upload(f"{session['seller_id']}/{image.filename}",
                                                                  image.read(),
                                                                  {"content_type": image.content_type})
                        image_url = sb.storage.from_("product-images").get_public_url(
                            f"{session['seller_id']}/{image.filename}")
                    expiry_value = datetime.strptime(expiry, "%Y-%m-%d") if expiry else None
                    product = Products(name=name, price=price_f, quantity=quantity_i, category=category,
                                       expiry=expiry_value, seller_id=session['seller_id'], image_url=image_url)
                    db.session.add(product)
                    db.session.commit()
                    return redirect(url_for("products", status="Product added successfully"))
            except ValueError:
                error = "Price and quantity must be valid numbers"

    return render_template("add_product.html", error=error)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    login_required(session)

    product = Products.query.filter_by(ID=product_id, seller_id=session['seller_id']).first()
    if not product or product.is_deleted:
        raise ItemNotFoundError("Product does not exist")

    return render_template("product_detail.html", product=product)


@app.route('/products/update/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    login_required(session)

    product = Products.query.filter_by(ID=product_id, seller_id=session['seller_id']).first_or_404()
    if request.method == 'POST':
        try:
            image = request.files.get('image')
            if image and image.filename:
                image_data = image.read()
                response = sb.storage.from_("product-images").upload(f"{session['seller_id']}/{image.filename}",
                                                                     image_data, {"content-type": image.content_type,
                                                                                  "upsert": "true"})
                product.image_url = sb.storage.from_("product-images").get_public_url(
                    f"{session['seller_id']}/{image.filename}") or None

            product.name = request.form.get('name', '').strip() or product.name
            product.price = float(request.form.get('price', product.price))
            product.quantity = int(request.form.get('quantity', product.quantity))
            product.category = request.form.get('category', '').strip() or product.category
            expiry = request.form.get('expiry') or None
            product.expiry = datetime.strptime(expiry, "%Y-%m-%d") if expiry else None

            if product.price < 0 or product.quantity < 0:
                return render_template("update_product.html", product=product,
                                       error="Price and quantity must be 0 or greater")
            db.session.commit()
            return redirect(url_for("products", status="Product updated successfully"))
        except ValueError:
            return render_template("update_product.html", product=product,
                                   error="Price and quantity must be valid numbers")

    return render_template("update_product.html", product=product)


@app.route('/products/delete/<int:product_id>', methods=['GET', 'POST'])
def delete_product(product_id):
    login_required(session)

    product = Products.query.filter_by(ID=product_id, seller_id=session['seller_id']).first_or_404()

    if request.method == 'POST':
        product.is_deleted = True
        db.session.commit()
        return redirect(url_for("products", status="Product deleted successfully"))

    return render_template("delete_product.html", product=product)


@app.route("/orders")
def orders():
    login_required(session)

    orders_list = Orders.query.filter_by(seller_id=session['seller_id']).all()
    return render_template("orders.html", orders=orders_list, status=request.args.get("status"),
                           error=request.args.get("error"))


@app.route("/order/create")
def create_order():
    login_required(session)

    products_list = Products.query.filter_by(seller_id=session['seller_id'], is_deleted=False).all()
    order_items = session.get("order_items", [])
    error = request.args.get("error")
    return render_template("create_order.html", products=products_list, order_items=order_items, error=error)


@app.route("/order/add-item", methods=["POST"])
def add_order_item():
    login_required(session)

    product_id = request.form.get("product_id")
    quantity = request.form.get("quantity")
    if not product_id or not quantity:
        return redirect(url_for("create_order", error="Missing product or quantity"))

    product = Products.query.filter_by(ID=int(product_id), seller_id=session['seller_id']).first()
    if not product:
        raise ItemNotFoundError("Product Not Found")

    try:
        qty = int(quantity)
        if qty < 1:
            raise ValueError("Quantity must be at least 1")
    except (ValueError, TypeError):
        return redirect(url_for("create_order", error="Invalid quantity"))
    items = session.get("order_items", [])
    items.append({
        "product_id": product.ID,
        "name": product.name,
        "quantity": qty,
        "price": product.price
    })
    session["order_items"] = items
    session.modified = True
    return redirect(url_for("create_order"))


@app.route("/order/remove-item", methods=["POST"])
def remove_order_item():
    login_required(session)
    try:
        index = int(request.form.get("index", -1))
    except (ValueError, TypeError):
        return redirect(url_for("create_order", error="Invalid item"))
    items = session.get("order_items", [])
    if 0 <= index < len(items):
        items.pop(index)
        session["order_items"] = items
        session.modified = True
    return redirect(url_for("create_order"))


@app.route("/order/submit", methods=["POST"])
def submit_order():
    login_required(session)
    items = session.get("order_items", [])
    order_type = request.form.get("order_type", "Outgoing")
    if not items:
        return redirect(url_for("create_order", error="Add at least one item"))

    # Check stock for Outgoing orders
    if order_type == "Outgoing":
        for i in items:
            product = Products.query.get(i["product_id"])
            if product and product.quantity < i["quantity"]:
                raise InsufficientStockError(
                    f"Not enough stock for {product.name} (have {product.quantity}, need {i['quantity']})")

    order = Orders(seller_id=session['seller_id'], type=order_type, total_price=0)
    db.session.add(order)
    db.session.commit()

    total = 0
    for i in items:
        product = Products.query.get(i["product_id"])
        if not product:
            continue
        db.session.add(
            OrderItems(order_id=order.ID, product_id=product.ID, quantity=i["quantity"], price=i["price"]))
        if order_type == "Incoming":
            product.quantity += i["quantity"]
        else:
            product.quantity -= i["quantity"]
        total += (i["quantity"] * i["price"])

    order.total_price = total
    db.session.commit()
    session.pop("order_items", None)
    return redirect(url_for("orders", status="Order created"))


@app.route("/order/<int:order_id>")
def order_detail(order_id):
    login_required(session)

    order = Orders.query.filter_by(ID=order_id, seller_id=session['seller_id']).first()
    if not order:
        return redirect(url_for("orders", error="Order not found"))

    order_items = OrderItems.query.filter_by(order_id=order.ID).all()
    detailed_items = []
    for item in order_items:
        product = Products.query.get(item.product_id)
        detailed_items.append({
            "id": item.ID,
            "product_name": product.name if product else "Deleted Product",
            "quantity": item.quantity,
            "price": item.price,
            "total": item.price * item.quantity
        })
    return render_template("order_detail.html", order=order, order_items=detailed_items)


if __name__ == '__main__':
    app.run()
