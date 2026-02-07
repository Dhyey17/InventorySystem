import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, session
from models import db, Sellers, Products, Orders, OrderItems

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
PORT = os.getenv("DB_PORT")
DBNAME = os.getenv("DB_NAME")
secrete = os.getenv("SECRETE_KEY")

# Construct the SQLAlchemy connection string
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = secrete
app.config["DEBUG"] = os.environ.get("FLASK_DEBUG") == "1"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

db.init_app(app)
with app.app_context():
    db.create_all()


@app.route('/')
def home():
    if session.get("seller_id"):
        return redirect(url_for("products"))
    return render_template("home.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        name = request.form['name'].strip()
        username = request.form['username'].strip()
        password = request.form['password'].strip()

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
            session["seller_id"] = user.ID
            return redirect(url_for('products'))
    return render_template('signup.html', error=error)


@app.route("/login", methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        user = Sellers.query.filter_by(username=username, password=password).first()
        if user:
            session["seller_id"] = user.ID
            return redirect(url_for('products'))
        else:
            error = 'Invalid Credentials'
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/products', methods=['GET'])
def products():
    if "seller_id" not in session:
        return redirect(url_for("login"))

    status = request.args.get('status')
    error = request.args.get("error")

    products_list = Products.query.filter_by(seller_id=session["seller_id"]).all()
    return render_template("products.html", products=products_list, status=status, error=error)


@app.route('/products/add', methods=['GET', 'POST'])
def add_product():
    if "seller_id" not in session:
        return redirect(url_for("login"))

    error = None

    if request.method == 'POST':
        name = request.form['name'].strip()
        price = request.form['price'].strip()
        quantity = request.form['quantity'].strip()
        category = request.form['category'].strip()
        expiry = request.form['expiry'].strip()

        if not name or not price or not quantity or not category:
            error = "All fields except expiry are required"

        else:
            expiry_value = (datetime.strptime(expiry, "%Y-%m-%d") if expiry else None)

            product = Products(name=name, price=float(price), quantity=int(quantity), category=category,
                               expiry=expiry_value, seller_id=session["seller_id"])
            db.session.add(product)
            db.session.commit()
            return redirect(url_for("products", status="Product added successfully"))

    return render_template("add_product.html", error=error)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    if "seller_id" not in session:
        return redirect(url_for("login"))

    product = Products.query.filter_by(ID=product_id, seller_id=session["seller_id"]).first()
    if not product:
        return redirect(url_for("products", error="Product not found"))

    return render_template("product_detail.html", product=product)


@app.route('/products/update/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    if "seller_id" not in session:
        return redirect(url_for("login"))

    product = Products.query.filter_by(ID=product_id, seller_id=session["seller_id"]).first_or_404()

    if request.method == 'POST':
        product.name = request.form['name']
        product.price = float(request.form['price'])
        product.quantity = int(request.form['quantity'])
        product.category = request.form['category']
        expiry = request.form['expiry'] or None
        product.expiry = (datetime.strptime(expiry, "%Y-%m-%d") if expiry else None)

        db.session.commit()
        return redirect(url_for("products", status="Product updated successfully"))

    return render_template("update_product.html", product=product)


@app.route('/products/delete/<int:product_id>', methods=['GET', 'POST'])
def delete_product(product_id):
    if "seller_id" not in session:
        return redirect(url_for("login"))

    product = Products.query.filter_by(ID=product_id, seller_id=session["seller_id"]).first_or_404()

    if request.method == 'POST':
        db.session.delete(product)
        db.session.commit()
        return redirect(url_for("products", status="Product deleted successfully"))

    return render_template("delete_product.html", product=product)


@app.route("/orders")
def orders():
    if "seller_id" not in session:
        return redirect(url_for("login"))

    orders_list = Orders.query.filter_by(seller_id=session["seller_id"]).all()
    return render_template("orders.html", orders=orders_list, status=request.args.get("status"))


@app.route("/order/create")
def create_order():
    products_list = Products.query.filter_by(seller_id=session["seller_id"]).all()
    order_items = session.get("order_items", [])
    return render_template("create_order.html", products=products_list, order_items=order_items)


@app.route("/order/add-item", methods=["POST"])
def add_order_item():
    product = Products.query.get_or_404(request.form["product_id"])

    items = session.get("order_items", [])
    items.append({
        "product_id": product.ID,
        "name": product.name,
        "quantity": int(request.form["quantity"]),
        "price": product.price
    })

    session["order_items"] = items
    session.modified = True
    return redirect(url_for("create_order"))


@app.route("/order/submit", methods=["POST"])
def submit_order():
    items = session.get("order_items", [])
    order_type = request.form["order_type"]
    if not items:
        return redirect(url_for("create_order"))

    order = Orders(seller_id=session["seller_id"], type=order_type, total_price=0)
    db.session.add(order)
    db.session.commit()

    total = 0
    for i in items:
        product = Products.query.get(i["product_id"])
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
    if "seller_id" not in session:
        return redirect(url_for("login"))

    order = Orders.query.filter_by(ID=order_id, seller_id=session["seller_id"]).first()
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
