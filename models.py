from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Sellers(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30),nullable=False)
    username = db.Column(db.String(50),nullable=False, unique=True)
    password = db.Column(db.String(50),nullable=False)

class Products(db.Model):
    ID =  db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.ID'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    expiry = db.Column(db.DateTime, nullable=False)
    category = db.Column(db.String(50), nullable=False)

class Orders(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('sellers.ID'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class OrderItems(db.Model):
    ID = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.ID'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.ID'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)