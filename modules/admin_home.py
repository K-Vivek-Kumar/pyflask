from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required


adminHome = Blueprint("adminHome", __name__)


@adminHome.route("/admin-home")
@jwt_required()
def admin_home():
    current_user = get_jwt_identity()
    print(current_user)
    if current_user["type"] != "admin":
        return jsonify({"error": "Protected Route"}), 403
    return jsonify({"admin": current_user["key"]}), 200
