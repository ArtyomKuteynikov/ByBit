# models.py

from flask_login import UserMixin
from . import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


class URLs(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(100), unique=True)
    tg_channel = db.Column(db.String(100))
    last_message_id = db.Column(db.String(100))
    tickers = db.Column(db.String(100))
    amount_1 = db.Column(db.REAL)
    amount_2 = db.Column(db.REAL)
    result_1 = db.Column(db.String(100))
    result_2 = db.Column(db.String(100))
    working = db.Column(db.Integer, default=1)
    stopped = db.Column(db.Integer, default=0)
    admins = db.Column(db.String(10000))


