from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..database import db
from ..models import Product


upload = Blueprint("upload", __name__)


@upload.route("/product-upload", methods=["POST"])
@jwt_required()
def product_upload():
    required_fields = [
        "name",
        "quantity",
        "category",
        "subCategory",
        "company",
        "description",
        "price",
        "discount",
    ]
    current_user = get_jwt_identity()
    if not current_user or current_user["type"] != "retailer":
        return jsonify({"error": "Protected Route"}), 403
    retailedId = current_user["id"]
    data = request.get_json()
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return (
            f"Missing required fields: {', '.join(missing_fields)}",
            400,
        )
    product_name = data["name"]
    product_quantity = data["quantity"]
    product_category = data["category"]
    product_sub_category = data["subCategory"]
    product_company = data["company"]
    product_description = data["description"]
    product_price = data["price"]
    product_discount = data["discount"]
    newProduct = Product(
        retailedId,
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
    return f"Product Uploaded", 200
