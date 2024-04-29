from datetime import datetime, timedelta
from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..database import db
from project.models import Cart, Order, Payments, Retailer, User


statics = Blueprint("statics", __name__)


@statics.route("/admin-stats")
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
