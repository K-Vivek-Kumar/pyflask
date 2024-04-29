from flask import Blueprint, jsonify

from project.models import Image


orderPreview = Blueprint("orderPreview", __name__)


@orderPreview.route("/image/<int:prodId>")
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


@orderPreview.route("/images/<int:prodId>")
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
