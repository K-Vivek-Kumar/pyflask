from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from project.models import Order, Product


pastOrders = Blueprint("pastOrders", __name__)


@pastOrders.route("/pending-orders")
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
