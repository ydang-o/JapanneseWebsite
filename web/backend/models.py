from datetime import datetime
from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255), nullable=False, default="ユーザー")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    points_balance = db.Column(db.Integer, nullable=False, default=0)


class PointTransaction(db.Model):
    __tablename__ = "point_transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    delta = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(255), nullable=False, default="調整")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("transactions", lazy=True)) 