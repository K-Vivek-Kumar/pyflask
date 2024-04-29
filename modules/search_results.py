from flask import Blueprint, jsonify, request
from sqlalchemy import or_

from project.models import Product


searchResults = Blueprint("searchResults", __name__)


@searchResults.route("/products")
def get_all_products():
    page_number = request.args.get("page", default=1, type=int)
    per_page = 10
    search_query = request.args.get("q", " ")

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
