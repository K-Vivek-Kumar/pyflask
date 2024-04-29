from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required


registrationConfirmation = Blueprint("registrationConfirmation", __name__)


@registrationConfirmation.route("/current-retailer")
@jwt_required()
def current_retailer():
    current_user = get_jwt_identity()
    print(current_user)
    if current_user["type"] != "retailer":
        return jsonify({"error": "Protected Route"}), 403
    return jsonify({"retailer": current_user["key"]}), 200


@registrationConfirmation.route("/current-user")
@jwt_required()
def current_user():
    current_user = get_jwt_identity()
    if current_user["type"] != "user":
        return jsonify({"error": "Protected Route"}), 403
    return jsonify({"user": current_user["key"]}), 200
