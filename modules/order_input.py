from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..database import db
from project.models import Order


orderInput = Blueprint("orderInput", __name__)


@orderInput.route("/order-the-product", methods=["POST"])
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
