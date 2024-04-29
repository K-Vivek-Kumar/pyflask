from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from project.models import User


viewProfile = Blueprint("viewProfile", __name__)


@viewProfile.route("/user-profile")
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
