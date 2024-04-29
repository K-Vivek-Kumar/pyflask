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
from flask import request, jsonify


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


@main.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    current_user = get_jwt_identity()
    if not current_user:
        return jsonify({"msg": "logout successful"})
    response = jsonify({"msg": "logout successful"})
    unset_jwt_cookies(response)
    return response


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


@main.route("/delete_address/<int:address_id>", methods=["POST"])
def delete_address(address_id):
    address = Address.query.get(address_id)

    if not address:
        return "Address not found", 404

    db.session.delete(address)
    db.session.commit()
    return "Address deleted successfully", 200


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


@main.route("/name")
def name():
    return "hello", 200


@main.route("/")
def hello_world():
    return "Connected"
