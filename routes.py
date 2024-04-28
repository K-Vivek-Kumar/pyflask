from datetime import datetime, timedelta
import os
import uuid
from bcrypt import checkpw, gensalt, hashpw
from flask import Blueprint, send_from_directory
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
    unset_jwt_cookies,
)

from .database import db
from .models import (
    Admin,
    Cart,
    Order,
    Payments,
    Product,
    Retailer,
    User,
    Image,
    Address,
)


main = Blueprint("main", __name__)


@main.route("/admin-stats")
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
    total_orders_price = db.session.query(db.func.sum(Order.price)).scalar()
    Payments_count = Payments.query.count()
    Payments_count_today = Payments.query.filter(
        Payments.payed_at >= twenty_four_hours_ago
    ).count()
    today = datetime.today().date()
    start_of_day = datetime.combine(today, datetime.min.time())
    end_of_day = datetime.combine(today, datetime.max.time())
    users_ordered_more_than_5 = len(
        set(cart.user_id for cart in Cart.query.all() if cart.quantity > 5)
    )
    users_ordered_more_than_10 = len(
        set(cart.user_id for cart in Cart.query.all() if cart.quantity > 10)
    )
    data = {
        "total_users": total_users,
        "new_users_last_24_hours": new_users_last_24_hours,
        "users_since_last_month": users_since_last_month,
        "total_retailers": total_retailers,
        "new_retailers_last_24_hours": new_retailers_last_24_hours,
        "retailers_since_last_month": retailers_since_last_month,
        "total_orders_price ": total_orders_price,
        "Payments_count": Payments_count,
        "Payments_count_today": Payments_count_today,
        "users_ordered_more_than_5": users_ordered_more_than_5,
        "users_ordered_more_than_10": users_ordered_more_than_10,
    }
    return jsonify({"data": data}), 200


@main.route("/pending-orders")
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


@main.route("/user-profile")
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


@main.route("/admin-login", methods=["POST"])
def admin_login():
    data = request.get_json()
    admin_email = data.get("email")
    admin_password = data.get("password")
    admin = Admin.query.filter_by(email=admin_email).first()
    print(admin_email, admin_password)
    if admin:
        if admin.password == admin_password:
            access_token = create_access_token(
                identity={"type": "admin", "key": admin.email}
            )
            response = {"access_token": access_token}
            return response
        else:
            return "Incorrect password", 401
    else:
        return "No such admin", 404


@main.route("/login", methods=["POST"])
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


@main.route("/retailer-login", methods=["POST"])
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


@main.route("/current-retailer")
@jwt_required()
def current_retailer():
    current_user = get_jwt_identity()
    print(current_user)
    if current_user["type"] != "retailer":
        return jsonify({"error": "Protected Route"}), 403
    return jsonify({"retailer": current_user["key"]}), 200


@main.route("/current-user")
@jwt_required()
def current_user():
    current_user = get_jwt_identity()
    if current_user["type"] != "user":
        return jsonify({"error": "Protected Route"}), 403
    return jsonify({"user": current_user["key"]}), 200


@main.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({"msg": "logout successful"})
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response


@main.route("/admin-home")
@jwt_required()
def admin_home():
    current_user = get_jwt_identity()
    print(current_user)
    if current_user["type"] != "admin":
        return jsonify({"error": "Protected Route"}), 403
    return jsonify({"admin": current_user["key"]}), 200


@main.route("/image/<int:prodId>")
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


@main.route("/images/<int:prodId>")
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


@main.route("/images/uploads/<filename>")
def get_image(filename):
    uploads_dir = "../uploads"
    try:
        return send_from_directory(uploads_dir, filename)

    except Exception as e:
        return jsonify({"error": "Image not found"}), 404


@main.route("/products/<int:prodId>")
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


@main.route("/add-admin", methods=["POST"])
@jwt_required()
def admin_add():
    current_user = get_jwt_identity()
    if current_user["type"] != "admin":
        return jsonify({"error": "Protected Route"}), 403
    data = request.get_json()
    admin_email = data.get("admin_email")
    admin_password = data.get("admin_password")
    new_admin = Admin(admin_email, admin_password)
    db.session.add(new_admin)
    db.session.commit()
    return "Admin added successfully", 200


@main.route("/update-phone-number", methods=["POST"])
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


@main.route("/cart")
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
            "id": product.id,
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


@main.route("/upload-cart", methods=["POST"])
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
        existing_cart_item.quantity += quantity
        db.session.commit()
        return jsonify({"message": "Quantity updated in Cart"}), 200
    else:
        new_cart_item = Cart(productId=product_id, userId=user_id, quantity=quantity)
        db.session.add(new_cart_item)
        db.session.commit()
        return jsonify({"message": "Added to Cart"}), 200


@main.route("/update_address/<int:address_id>", methods=["POST"])
def update_address(address_id):
    address = Address.query.get(address_id)

    if not address:
        return "Address not found", 404

    address.address = request.form["address"]
    address.city = request.form["city"]
    address.postal_code = request.form["postal_code"]

    db.session.commit()
    return "Address updated successfully"


@main.route("/make-payment", methods=["POST"])
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


@main.route("/order-the-product", methods=["POST"])
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


@main.route("/address")
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


@main.route("/add-address", methods=["POST"])
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
    except Exception as e:
        db.session.rollback()
        return f"Error: {e}"


@main.route("/delete_address/<int:address_id>", methods=["POST"])
def delete_address(address_id):
    address = Address.query.get(address_id)

    if not address:
        return "Address not found", 404

    db.session.delete(address)
    db.session.commit()
    return "Address deleted successfully", 200


from flask import request, jsonify
from sqlalchemy import or_


@main.route("/products")
def get_products():
    page_number = request.args.get("page", default=1, type=int)
    per_page = 10
    search_query = request.args.get("q", "")

    products = Product.query.filter(
        or_(
            Product.name.ilike(f"%{search_query}%"),
            Product.description.ilike(f"%{search_query}%"),
            Product.category.ilike(f"%{search_query}%"),
            Product.sub_category.ilike(f"%{search_query}%"),
        )
    ).paginate(page=page_number, per_page=per_page, error_out=False)

    product_list = []
    for product in products.items:
        if not product.active:
            print(f"Skipping inactive product: {product.name}")
            continue
        print(f"Adding active product: {product.name}")
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
        "next_page": products.next_num if products.has_next else None,
        "prev_page": products.prev_num if products.has_prev else None,
    }

    return jsonify(response)


@main.route("/uploads", methods=["POST"])
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
        unique_filename = (
            str(uuid.uuid4()) + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        file_extension = os.path.splitext(file.filename)[1]
        if file_extension:
            unique_filename += file_extension
        file.save(os.path.join("uploads", unique_filename))
        print("Reached")
        new_image = Image(product_id=productId, fileName=unique_filename)
        print("Reached")
        db.session.add(new_image)
        db.session.commit()

        return jsonify({"message": "File uploaded successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


@main.route("/signup", methods=["POST"])
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


@main.route("/retailer-signup", methods=["POST"])
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


@main.route("/push-status/<int:order_id>", methods=["POST"])
@jwt_required()
def push_prod(order_id):
    current_user = get_jwt_identity()
    if current_user["type"] != "retailer":
        return jsonify({"error": "Unauthorized"}), 403
    retailedId = current_user["id"]
    order = Order.query.filter_by(id=order_id).first()
    prodId = order.product_id
    product = Product.query.filter_by(id=prodId).first()
    if product.retailer_id == retailedId:
        if order.status == 0:
            return "Payment yet to be done"
        elif order.status == 1:
            order.status = 2
        elif order.status == 2:
            order.status = 3
            order.date_of_delivery = datetime.today()
        db.session.commit()
        return "Status Pushed", 200
    else:
        return "Protected area", 403


@main.route("/activate/<int:product_id>", methods=["POST"])
@jwt_required()
def activate_prod(product_id):
    current_user = get_jwt_identity()
    if current_user["type"] != "retailer":
        return jsonify({"error": "Unauthorized"}), 403
    retailedId = current_user["id"]
    prod = Product.query.filter_by(id=product_id).first()
    if prod.retailer_id == retailedId:
        if prod.quantity > 0:
            c = Image.query.filter_by(product_id=prod.id).count()
            if c < 1:
                return "Upload images to activate", 200
            if prod.active == False:
                prod.active = True
            else:
                prod.active = False
            db.session.commit()
            return "Done", 200
        else:
            return "Product quantity insufficient", 200
    else:
        return "Protected area", 403


@main.route("/active-orders")
@jwt_required()
def active_orders():
    current_user = get_jwt_identity()
    if current_user["type"] != "retailer":
        return jsonify({"error": "Unauthorized"}), 403
    retailedId = current_user["id"]
    prods = Order.query.all()
    ret_orders = []
    for prod in prods:
        isYes = Product.query.filter_by(id=prod.product_id).first()
        if isYes and isYes.retailer_id == retailedId:
            add = Address.query.filter_by(id=prod.address).first()
            order_data = {
                "id": prod.id,
                "product_id": prod.product_id,
                "address": f"{add.address}, {add.city}, {add.postal_code}",
                "quantity": prod.quantity,
                "cash_on_delivery": prod.cash_on_delivery,
                "price": prod.price,
                "status": prod.status,
                "date_of_order": prod.date_of_order.strftime("%Y-%m-%d %H:%M:%S"),
            }
            ret_orders.append(order_data)
    return jsonify({"order": ret_orders}), 200


@main.route("/inventory")
@jwt_required()
def inventory():
    current_user = get_jwt_identity()
    if current_user["type"] != "retailer":
        return jsonify({"error": "Unauthorized"}), 403
    retailedId = current_user["id"]
    items = Product.query.filter_by(retailer_id=retailedId).all()
    item_to = []
    for item in items:
        eachItem = {
            "id": item.id,
            "name": item.name,
            "quantity": item.quantity,
            "category": item.category,
            "sub_category": item.sub_category,
            "company": item.company,
            "description": item.description,
            "price": item.price,
            "discount": item.discount,
            "active": item.active,
        }
        item_to.append(eachItem)
    return jsonify({"items": item_to}), 200


@main.route("/name")
def name():
    return "hello", 200


@main.route("/")
def hello_world():
    return "Connected"
