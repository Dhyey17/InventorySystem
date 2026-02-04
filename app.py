from flask import Flask, request, render_template, redirect, url_for, session
from dotenv import load_dotenv
import os
from models import db, Sellers

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
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

db.init_app(app)
with app.app_context():
    db.create_all()


@app.route('/')
def home():
    return render_template("home.html")


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        name = request.form['name'].strip()
        username = request.form['username'].strip()
        password = request.form['password'].strip()

        if not name:
            error = 'Name is cannot be empty'
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
            return redirect(url_for('dashboard'))
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
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid Credentials'
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route("/dashboard")
def dashboard():
    return "This is Dashboard"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
