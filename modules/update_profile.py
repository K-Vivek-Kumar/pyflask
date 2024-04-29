from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..database import db
from project.models import Address, User


updateProfile = Blueprint("updateProfile", __name__)


@updateProfile.route("/add-address", methods=["POST"])
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


@updateProfile.route("/update-phone-number", methods=["POST"])
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
