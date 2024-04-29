from datetime import datetime

from sqlalchemy import Boolean
from .database import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(10), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.today)

    def __init__(self, name, email, password) -> None:
        self.name = name
        self.email = email
        self.password = password

    def __repr__(self) -> str:
        return f"<User {self.id}>"


class Address(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", backref=db.backref("addresses", lazy=True))
    address = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    postal_code = db.Column(db.String(10), nullable=False)

    def __init__(self, user_id, address, city, postal_code):
        self.user_id = user_id
        self.address = address
        self.city = city
        self.postal_code = postal_code

    def __repr__(self):
        return f"<Address {self.id}>"


class Retailer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.today)

    def __init__(self, name, email, password, phone_number, address) -> None:
        self.name = name
        self.email = email
        self.password = password
        self.phone_number = phone_number
        self.address = address

    def __repr__(self) -> str:
        return f"<Retailer {self.id}>"


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    retailer_id = db.Column(db.Integer, db.ForeignKey("retailer.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    sub_category = db.Column(db.String(50), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    active = db.Column(Boolean, default=False)

    def __init__(
        self,
        retailerId,
        name,
        quantity,
        category,
        sub_category,
        company,
        description,
        price,
        discount=0,
    ) -> None:
        self.name = name
        self.retailer_id = retailerId
        self.quantity = quantity
        self.category = category
        self.sub_category = sub_category
        self.company = company
        self.description = description
        self.price = price
        self.discount = discount

    def __repr__(self) -> str:
        return f"<ProductUpload {self.id}>"


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    filename = db.Column(db.String(200), nullable=False)

    def __init__(self, product_id, fileName):
        self.product_id = product_id
        self.filename = fileName

    def __repr__(self) -> str:
        return f"<Image {self.id}>"


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)

    def __init__(self, productId, userId, quantity) -> None:
        self.product_id = productId
        self.user_id = userId
        self.quantity = quantity

    def __repr__(self) -> str:
        return f"<CartItem {self.id}>"


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    address = db.Column(db.Integer, db.ForeignKey("address.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    cash_on_delivery = db.Column(Boolean, default=False, nullable=False)
    price = db.Column(db.Float, nullable=False)
    status = db.Column(db.Integer, default=0, nullable=False)
    date_of_order = db.Column(db.DateTime, default=datetime.today, nullable=False)
    date_of_delivery = db.Column(db.DateTime)

    def _init_(
        self,
        user_id,
        product_id,
        quantity,
        address,
        cash_on_delivery,
        price,
        status=0,
        date_of_order=datetime.today,
        date_of_delivery=None,
    ) -> None:
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity
        self.address = address
        self.cash_on_delivery = cash_on_delivery
        self.price = price
        self.status = status
        self.date_of_order = date_of_order
        self.date_of_delivery = date_of_delivery

    def __repr__(self) -> str:
        return f"<Order {self.id}>"


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.today)

    def __init__(self, email, password) -> None:
        self.email = email
        self.password = password


class Payments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    payed_at = db.Column(db.DateTime, default=datetime.today)

    def __init__(self, order_id) -> None:
        self.order_id = order_id
