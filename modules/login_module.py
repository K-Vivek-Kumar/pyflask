from bcrypt import checkpw
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from project.models import Admin, Retailer, User


login = Blueprint("login", __name__)


@login.route("/admin-login", methods=["POST"])
def admin_login():
    data = request.get_json()
    admin_email = data.get("email")
    admin_password = data.get("password")
    admin = Admin.query.filter_by(email=admin_email).first()
    print(admin_email, admin_password)
    if admin:
        if admin.password == admin_password:
            access_token = create_access_token(
                identity={"type": "admin", "key": admin.email}
            )
            response = {"access_token": access_token}
            return response
        else:
            return "Incorrect password", 401
    else:
        return "No such admin", 404


@login.route("/login", methods=["POST"])
def user_login():
    if request.method == "POST":
        data = request.get_json()
        user_email = data.get("email")
        user_password = data.get("password")
        user = User.query.filter_by(email=user_email).first()
        if user:
            if checkpw(user_password.encode("utf-8"), user.password.encode("utf-8")):
                access_token = create_access_token(
                    identity={"type": "user", "key": user_email, "id": user.id}
                )
                response = {"access_token": access_token}
                return jsonify(response)
            else:
                return "Incorrect password", 401
        else:
            return "No such user", 404


@login.route("/retailer-login", methods=["POST"])
def retailer_login():
    data = request.get_json()
    retailer_email = data.get("email")
    retailer_password = data.get("password")
    user: Retailer = Retailer.query.filter_by(email=retailer_email).first()
    if user:
        stored_hashed_password = user.password.encode("utf-8")
        provided_password = retailer_password.encode("utf-8")

        if checkpw(provided_password, stored_hashed_password):
            access_token = create_access_token(
                identity={"type": "retailer", "key": retailer_email, "id": user.id}
            )
            response = {"access_token": access_token}
            return response
        else:
            return f"Incorrect Password", 401
    else:
        return "No such user", 404
