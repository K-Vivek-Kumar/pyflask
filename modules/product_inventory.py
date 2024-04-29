from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from project.models import Product


productInventory = Blueprint("productInventory", __name__)


@productInventory.route("/inventory")
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
