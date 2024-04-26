from datetime import datetime, timedelta
import os
from MySQLdb import IntegrityError
from flask import Flask, g, jsonify, redirect, request, send_from_directory, session
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt_identity,
    jwt_required,
    unset_jwt_cookies,
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean
from bcrypt import hashpw, gensalt, checkpw


app = Flask(__name__)
CORS(app, supports_credentials=True)
db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/dev"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["JWT_SECRET_KEY"] = "please-remember-to-change-me"

# app.config["SESSION_TYPE"] = "sqlalchemy"
app.config["SECRET_KEY"] = "Vivek Kum"
# app.config["SESSION_SQLALCHEMY"] = db
jwt = JWTManager(app)
db.init_app(app)


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
    description = db.Column(db.String(500), nullable=False)
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


@app.route("/admin-stats")
@jwt_required()
def stats():
    current_user = get_jwt_identity()
    if current_user["type"] != "admin":
        return jsonify({"error": "Protected Route"}), 403
    total_users = User.query.count()
    twenty_four_hours_ago = datetime.today() - timedelta(hours=24)
    new_users_last_24_hours = User.query.filter(
        User.created_at >= twenty_four_hours_ago
    ).count()
    one_month_ago = datetime.today() - timedelta(days=30)
    users_since_last_month = User.query.filter(User.created_at >= one_month_ago).count()
    total_retailers = Retailer.query.count()

    twenty_four_hours_ago = datetime.today() - timedelta(hours=24)
    new_retailers_last_24_hours = Retailer.query.filter(
        Retailer.created_at >= twenty_four_hours_ago
    ).count()

    one_month_ago = datetime.today() - timedelta(days=30)
    retailers_since_last_month = Retailer.query.filter(
        Retailer.created_at >= one_month_ago
    ).count()
    data = {
        "total_users": total_users,
        "new_users_last_24_hours": new_users_last_24_hours,
        "users_since_last_month": users_since_last_month,
        "total_retailers": total_retailers,
        "new_retailers_last_24_hours": new_retailers_last_24_hours,
        "retailers_since_last_month": retailers_since_last_month,
    }
    return jsonify({"data": data}), 200


@app.route("/pending-orders")
@jwt_required()
def pending_orders():
    current_user = get_jwt_identity()
    if current_user["type"] != "user":
        return jsonify({"error": "Protected Route"}), 403
    user_id = current_user["id"]
    allOrders = Order.query.filter_by(user_id=int(user_id)).all()
    order_list = []
    for order in allOrders:
        order_data = {
            "order_id": order.id,
            "product_id": order.product_id,
            "product_name": Product.query.filter_by(id=order.product_id).first().name,
            "status": order.status,
            "cash_on_delivery": order.cash_on_delivery,
            "date_of_order": order.date_of_order.strftime("%Y-%m-%d %H:%M:%S"),
            "date_of_delivery": (
                order.date_of_delivery.strftime("%Y-%m-%d %H:%M:%S")
                if order.date_of_delivery
                else None
            ),
            "price": order.price,
        }
        order_list.append(order_data)

    return jsonify({"allOrders": order_list}), 200


@app.route("/user-profile")
@jwt_required()
def user_profile():
    current_user = get_jwt_identity()
    if current_user["type"] != "user":
        return jsonify({"error": "Protected Route"}), 403
    user_id = current_user["id"]
    user = User.query.filter_by(id=user_id).first()
    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone_number": user.phone_number,
        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }
    return jsonify({"user": user_data}), 200


@app.route("/admin-login", methods=["POST"])
def admin_login():
    data = request.get_json()
    admin_email = data.get("email")
    admin_password = data.get("password")
    admin = Admin.query.filter_by(email=admin_email).first()
    print(admin_email, admin_password)
    if admin:
        stored_hashed_password = admin.password.encode("utf-8")
        provided_password = admin_password.encode("utf-8")

        if checkpw(provided_password, stored_hashed_password):
            access_token = create_access_token(
                identity={"type": "admin", "key": admin.email}
            )
            response = {"access_token": access_token}
            return response
        else:
            return "Incorrect password", 401
    else:
        return "No such admin", 404


@app.route("/login", methods=["POST"])
def user_login():
    if request.method == "POST":
        data = request.get_json()
        user_email = data.get("email")
        user_password = data.get("password")
        user = User.query.filter_by(email=user_email).first()
        if user:
            if checkpw(user_password.encode("utf-8"), user.password.encode("utf-8")):
                access_token = create_access_token(
                    identity={"type": "user", "key": user_email, "id": user.id}
                )
                response = {"access_token": access_token}
                return jsonify(response)
            else:
                return "Incorrect password", 401
        else:
            return "No such user", 404


@app.route("/retailer-login", methods=["POST"])
def retailer_login():
    data = request.get_json()
    retailer_email = data.get("email")
    retailer_password = data.get("password")
    user: Retailer = Retailer.query.filter_by(email=retailer_email).first()
    if user:
        stored_hashed_password = user.password.encode("utf-8")
        provided_password = retailer_password.encode("utf-8")

        if checkpw(provided_password, stored_hashed_password):
            access_token = create_access_token(
                identity={"type": "retailer", "key": retailer_email, "id": user.id}
            )
            response = {"access_token": access_token}
            return response
        else:
            return f"Incorrect Password", 401
    else:
        return "No such user", 404


@app.route("/current-retailer")
@jwt_required()
def current_retailer():
    current_user = get_jwt_identity()
    print(current_user)
    if current_user["type"] != "retailer":
        return jsonify({"error": "Protected Route"}), 403
    return jsonify({"retailer": current_user["key"]}), 200


@app.route("/current-user")
@jwt_required()
def current_user():
    current_user = get_jwt_identity()
    print(current_user)
    if current_user["type"] != "user":
        return jsonify({"error": "Protected Route"}), 403
    return jsonify({"user": current_user["key"]}), 200


@app.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({"msg": "logout successful"})
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response


@app.route("/admin-home")
@jwt_required()
def admin_home():
    current_user = get_jwt_identity()
    print(current_user)
    if current_user["type"] != "admin":
        return jsonify({"error": "Protected Route"}), 403
    return jsonify({"admin": current_user["key"]}), 200


@app.route("/image/<int:prodId>")
def show_images_one(prodId):
    try:
        filename = (
            Image.query.filter_by(product_id=prodId)
            .with_entities(Image.filename)
            .first()
        )
        filename = filename[0]
        image_urls = [f"/images/uploads/{filename}"]
        return jsonify({"images": image_urls}), 200
    except Exception as e:
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/images/<int:prodId>")
def show_images(prodId):
    try:
        filenames = (
            Image.query.filter_by(product_id=prodId).with_entities(Image.filename).all()
        )
        image_filenames = [filename[0] for filename in filenames]
        image_urls = [f"/images/uploads/{filename}" for filename in image_filenames]
        return jsonify({"images": image_urls}), 200
    except Exception as e:
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/images/uploads/<filename>")
def get_image(filename):
    uploads_dir = app.config["UPLOAD_FOLDER"]
    try:
        return send_from_directory(uploads_dir, filename)

    except Exception as e:
        return jsonify({"error": "Image not found"}), 404


@app.route("/products/<int:prodId>")
def show_product(prodId):
    print("received: ", prodId)
    try:
        product = Product.query.filter_by(id=int(prodId)).first()
        print(product)
        if product:
            product_data = {
                "name": product.name,
                "quantity": product.quantity,
                "category": product.category,
                "sub_category": product.sub_category,
                "company": product.company,
                "description": product.description,
                "price": product.price,
                "discount": product.discount,
            }
            return jsonify(product_data), 200
        else:
            return jsonify({"error": "Product not found"}), 404
    except Exception as e:
        print(f"Error fetching product: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500


@app.route("/add-admin", methods=["POST"])
@jwt_required()
def admin_add():
    data = request.get_json()
    admin_email = data.get("admin_email")
    admin_password = data.get("admin_password")
    hashed_password = hashpw(admin_password.encode("utf-8"), gensalt())
    new_admin = Admin(admin_email, hashed_password)
    db.session.add(new_admin)
    db.session.commit()
    return "Admin added successfully", 200


@app.route("/update-phone-number", methods=["POST"])
@jwt_required()
def newPhoneNumber():
    current_user = get_jwt_identity()
    if current_user["type"] != "user":
        return jsonify({"error": "Protected Route"}), 403
    user_id = current_user["id"]
    user: User = User.query.filter_by(id=int(user_id)).first()
    data = request.get_json()
    phoneNo = data.get("phoneNo")
    user.phone_number = phoneNo
    db.session.commit()
    return "Phone Number Updated", 200


@app.route("/cart")
@jwt_required()
def cart_items():
    current_user = get_jwt_identity()
    if current_user["type"] != "user":
        return jsonify({"error": "Protected Route"}), 403
    user_id = current_user["id"]
    items = Cart.query.filter_by(user_id=int(user_id))
    products = []
    for item in items:
        prodId = item.product_id
        product = Product.query.filter_by(id=prodId).first()
        product_data = {
            "name": product.name,
            "category": product.category,
            "sub_category": product.sub_category,
            "company": product.company,
            "description": product.description,
            "price": product.price,
            "discount": product.discount,
            "quantity": item.quantity,
        }
        products.append(product_data)
    response = {"Items": products}
    return jsonify(response), 200


@app.route("/upload-cart", methods=["POST"])
@jwt_required()
def cart_upload():
    current_user = get_jwt_identity()
    if current_user["type"] != "user":
        return jsonify({"error": "Protected Route"}), 403
    user_id = current_user["id"]
    data = request.get_json()
    product_id = data.get("product_id")
    quantity = data.get("quantity")
    existing_cart_item = Cart.query.filter_by(
        product_id=product_id, user_id=user_id
    ).first()

    if existing_cart_item:
        existing_cart_item.quantity = quantity
        db.session.commit()
        return jsonify({"message": "Quantity updated in Cart"}), 200
    else:
        new_cart_item = Cart(productId=product_id, userId=user_id, quantity=quantity)
        db.session.add(new_cart_item)
        db.session.commit()
        return jsonify({"message": "Added to Cart"}), 200


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


@app.route("/make-payment", methods=["POST"])
@jwt_required()
def make_payment():
    current_user = get_jwt_identity()
    if current_user["type"] != "user":
        return jsonify({"error": "Protected Route"}), 403
    user_id = current_user["id"]
    orderId = request.get_json().get("orderId")
    newPayment = Payments(order_id=orderId)
    orderMade: Order = Order.query.filter_by(id=orderId).first()
    if orderMade.status == 0 and not orderMade.cash_on_delivery:
        orderMade.status = 1
        db.session.add(newPayment)
    db.session.commit()
    return "Payment Done Successfully", 200


@app.route("/order-the-product", methods=["POST"])
@jwt_required()
def order_product():
    current_user = get_jwt_identity()
    if current_user["type"] != "user":
        return jsonify({"error": "Protected Route"}), 403
    user_id = current_user["id"]
    try:
        data = request.get_json()
        product_id = data.get("product_id")
        address_id = data.get("address_id")
        quantity = data.get("quantity")
        cash_on_delivery = data.get("cash_on_delivery")
        if cash_on_delivery:
            stat = 1
        else:
            stat = 0
        price = data.get("price")
        new_order = Order(
            user_id=user_id,
            product_id=product_id,
            address=address_id,
            quantity=quantity,
            cash_on_delivery=cash_on_delivery,
            status=stat,
            price=price,
        )
        db.session.add(new_order)
        db.session.commit()
        return "Done"
    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({"error": str(e)}), 500


@app.route("/address")
@jwt_required()
def userAddresses():
    current_user = get_jwt_identity()
    if current_user["type"] != "user":
        return jsonify({"error": "Protected Route"}), 403
    user_id = current_user["id"]
    try:
        addresses = Address.query.filter_by(user_id=user_id).all()
        serialized_addresses = [
            {
                "id": address.id,
                "address": address.address,
                "city": address.city,
                "postal_code": address.postal_code,
            }
            for address in addresses
        ]
        return jsonify({"Addresses": serialized_addresses}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/add-address", methods=["POST"])
@jwt_required()
def add_address():
    current_user = get_jwt_identity()
    if current_user["type"] != "user":
        return jsonify({"error": "Protected Route"}), 403
    user_id = current_user["id"]
    data = request.get_json()
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


@app.route("/product-upload", methods=["POST"])
@jwt_required()
def product_upload():
    current_user = get_jwt_identity()
    if not current_user or current_user["type"] != "retailer":
        return jsonify({"error": "Protected Route"}), 403
    retailedId = current_user["id"]
    data = request.get_json()
    product_retailer = retailedId
    product_name = data.get("name")
    product_quantity = data.get("quantity")
    product_category = data.get("category")
    product_sub_category = data.get("subCategory")
    product_company = data.get("company")
    product_description = data.get("description")
    product_price = data.get("price")
    product_discount = data.get("discount")
    newProduct = Product(
        product_retailer,
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


@app.route("/products")
def get_products():
    page_number = request.args.get("page", default=1, type=int)
    per_page = 10

    products = Product.query.paginate(
        page=page_number, per_page=per_page, error_out=False
    )

    product_list = []
    for product in products.items:
        product_data = {
            "id": product.id,
            "name": product.name,
            "quantity": product.quantity,
            "category": product.category,
            "sub_category": product.sub_category,
            "company": product.company,
            "description": product.description,
            "price": product.price,
            "discount": product.discount,
            "active": product.active,
        }
        product_list.append(product_data)

    response = {
        "products": product_list,
        "page": products.page,
        "has_next": products.has_next,
        "has_prev": products.has_prev,
        "next_page": products.next_num,
        "prev_page": products.prev_num,
    }

    return jsonify(response)


@app.route("/uploads", methods=["POST"])
@jwt_required()
def upload_image():
    current_user = get_jwt_identity()
    if current_user["type"] != "retailer":
        return jsonify({"error": "Unauthorized"}), 403
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    productId = int(request.form.get("product_id"))
    print(file, productId)

    if not file:
        return jsonify({"error": "No file provided"}), 400

    if not productId:
        return jsonify({"error": "Product ID not provided"}), 400

    try:
        file_name = file.filename
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], file_name))
        new_image = Image(product_id=productId, fileName=file_name)
        db.session.add(new_image)
        db.session.commit()

        return jsonify({"message": "File uploaded successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/signup", methods=["POST"])
def user_signup():
    data = request.get_json()
    user_email = data.get("email")
    user_name = data.get("name")
    user_password = data.get("password")
    hashed_password = hashpw(user_password.encode("utf-8"), gensalt())
    new_user = User(user_name, user_email, hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return f"{user_name} is registered", 200


@app.route("/retailer-signup", methods=["POST"])
def retailer_signup():
    data = request.get_json()
    retailer_email = data.get("email")
    retailer_name = data.get("name")
    retailer_password = data.get("password")
    hashed_password = hashpw(retailer_password.encode("utf-8"), gensalt())
    retailer_phone_number = data.get("phoneNo")
    retailer_address = data.get("address")
    new_user = Retailer(
        retailer_name,
        retailer_email,
        hashed_password,
        retailer_phone_number,
        retailer_address,
    )
    db.session.add(new_user)
    db.session.commit()
    return f"{retailer_name} is registered", 200


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
