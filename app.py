import os
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, session
from models import db, Sellers, Products

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST")
PORT = os.getenv("DB_PORT")
DBNAME = os.getenv("DB_NAME")

# Construct the SQLAlchemy connection string
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = "dev-secret-key"

db.init_app(app)
with app.app_context():
    db.create_all()


@app.route('/')
def home():
    if session.get("seller_id"):
        return redirect(url_for("products"))
    return render_template("home.html", session=session)


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

    products = Products.query.filter_by(seller_id=session["seller_id"]).all()
    return render_template("products.html", products=products, status=status, error=error)


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


if __name__ == '__main__':
    app.run(debug=True)
