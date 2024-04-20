from datetime import datetime, timedelta
import os
from MySQLdb import IntegrityError
from flask import Flask, jsonify, request, redirect, session
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean


app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/dev"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"
app.secret_key = "I am a Good Boy"
app.permanent_session_lifetime = timedelta(days=7)
db = SQLAlchemy(app)
CORS(app)


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
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    sub_category = db.Column(db.String(50), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Float, default=0)
    active = db.Column(Boolean, default=False)

    def __init__(
        self,
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


@app.route("/admin-login", methods=["POST"])
def admin_login():
    admin_email = request.form["email"]
    admin_password = request.form["password"]
    admin = Admin.query.filter_by(email=admin_email).first()
    if admin:
        if admin.password == admin_password:
            session["admin_id"] = admin.id
            return f"{admin.id}"
        else:
            return f"{admin.password}"
    else:
        return "No such user"


@app.route("/add-admin", methods=["POST"])
def admin_add():
    data = request.get_json()
    admin_email = data.get("admin_email")
    admin_password = data.get("admin_password")
    new_admin = Admin(admin_email, admin_password)

    db.session.add(new_admin)
    db.session.commit()
    return "Done"


@app.route("/order-the-product", methods=["POST"])
def order_product():
    try:
        data = request.get_json()
        user_id = data.get("user_id")
        product_id = data.get("product_id")
        address_id = data.get("address_id")
        quantity = data.get("quantity")
        cash_on_delivery = data.get("cash_on_delivery")
        price = data.get("price")
        new_order = Order(
            user_id=user_id,
            product_id=product_id,
            address=address_id,
            quantity=quantity,
            cash_on_delivery=cash_on_delivery,
            price=price,
        )
        db.session.add(new_order)
        db.session.commit()
        return "Done"
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({"error": str(e)}), 500


@app.route("/upload-cart", methods=["POST"])
def cart_upload():
    product_id = request.form["product_id"]
    user_id = request.form["user_id"]
    quantity = request.form["quantity"]
    newCart = Cart(product_id, user_id, quantity)
    db.session.add(newCart)
    db.session.commit()
    return "Added to Cart"


@app.route("/update_address/<int:address_id>", methods=["POST"])
def update_address(address_id):
    address = Address.query.get(address_id)

    if not address:
        return "Address not found", 404

    address.address = request.form["address"]
    address.city = request.form["city"]
    address.postal_code = request.form["postal_code"]

    db.session.commit()
    return "Address updated successfully"


@app.route("/add_address", methods=["POST"])
def add_address():
    data = request.get_json()

    user_id = data.get("user_id")
    address = data.get("address")
    city = data.get("city")
    postal_code = data.get("postal_code")

    if not all([user_id, address, city, postal_code]):
        return "Missing"

    try:
        new_address = Address(
            user_id=user_id, address=address, city=city, postal_code=postal_code
        )

        db.session.add(new_address)
        db.session.commit()

        return "Done"
    except IntegrityError:
        db.session.rollback()
        return "No such User"
    except Exception as e:
        db.session.rollback()
        return f"Error: {e}"


@app.route("/delete_address/<int:address_id>", methods=["POST"])
def delete_address(address_id):
    address = Address.query.get(address_id)

    if not address:
        return "Address not found", 404

    db.session.delete(address)
    db.session.commit()
    return "Address deleted successfully", 200


@app.route("/phone", methods=["POST"])
def update_phone():
    if "user_id" in session:
        user_id = session["user_id"]
        user: User = User.query.get(user_id)
        if not user:
            return "User not found", 404
        new_phone = request.form.get("phone")
        if new_phone:
            user.phone_number = new_phone
            db.session.commit()
            return "Address updated successfully", 200
        else:
            return "Address not provided", 400
    else:
        return "Login Required", 401


@app.route("/login", methods=["POST"])
def user_login():
    if request.method == "POST":
        user_email = request.form["email"]
        user_password = request.form["password"]
        user = User.query.filter_by(email=user_email).first()
        if user:
            if user.password == user_password:
                session["user_id"] = user.id
                return f"{user.id}"
            else:
                return f"{user.password}"
        else:
            return "No such user"


@app.route("/product-upload", methods=["POST"])
def product_upload():
    if "retailer_id" not in session:
        return "Login Error"
    product_name = request.form["name"]
    product_quantity = request.form["quantity"]
    product_category = request.form["category"]
    product_sub_category = request.form["sub-category"]
    product_company = request.form["company"]
    product_description = request.form["description"]
    product_price = request.form["price"]
    product_discount = request.form["discount"]
    newProduct = Product(
        product_name,
        product_quantity,
        product_category,
        product_sub_category,
        product_company,
        product_description,
        product_price,
        product_discount,
    )
    db.session.add(newProduct)
    db.session.commit()
    return "Product Uploaded"


@app.route("/uploads", methods=["POST"])
def upload_image():
    if "retailer_id" not in session:
        return "Login Error"
    file = request.files["file"]
    product_id = request.form["product_id"]
    if file:
        file_name = f"{file.filename}"
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], file_name))
        newFile = Image(product_id, file_name)
        db.session.add(newFile)
        db.session.commit()
        return "File Uploaded"
    return "Retry"


@app.route("/signup", methods=["POST"])
def user_signup():
    user_email = request.form["email"]
    user_name = request.form["name"]
    user_password = request.form["password"]
    new_user = User(user_name, user_email, user_password)
    db.session.add(new_user)
    db.session.commit()
    session["user_id"] = new_user.id
    return f"{user_name} is registered"


@app.route("/retailer-login", methods=["POST"])
def retailer_login():
    retailer_email = request.form["email"]
    retailer_password = request.form["password"]
    user: Retailer = Retailer.query.filter_by(email=retailer_email).first()
    if user:
        if user.password == retailer_password:
            session["retailer_id"] = user.id
            return f"{user.id}"
        else:
            return f"Incorrect Password"
    else:
        return "No such user"


@app.route("/retailer-signup", methods=["POST"])
def retailer_signup():
    retailer_email = request.form["email"]
    retailer_name = request.form["name"]
    retailer_password = request.form["password"]
    retailer_phone_number = request.form["phoneNo"]
    retailer_address = request.form["address"]
    new_user = Retailer(
        retailer_name,
        retailer_email,
        retailer_password,
        retailer_phone_number,
        retailer_address,
    )
    db.session.add(new_user)
    db.session.commit()
    session["retailer_id"] = new_user.id
    return f"{retailer_name} is registered"


@app.route("/name")
def name():
    if "user_id" in session:
        user_id = session["user_id"]
        return f"User ID: {user_id}"
    else:
        return "User ID not found in session"


@app.route("/retailer-name")
def retailer_name():
    if "retailer_id" in session:
        user_id = session["retailer_id"]
        return f"Retailer ID: {user_id}"
    else:
        return "Retailer ID not found in session"


@app.route("/")
def hello_world():
    return "Connected"


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
