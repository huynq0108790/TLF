from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    buy_price = db.Column(db.Float, nullable=False)
    target1 = db.Column(db.Float, nullable=True)
    target2 = db.Column(db.Float, nullable=True)
    cut_loss = db.Column(db.Float, nullable=True)
    note = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())  # Thêm cột timestamp

    def __repr__(self):
        return f'<Stock {self.symbol}>'
