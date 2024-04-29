from bcrypt import gensalt, hashpw
from flask import Blueprint, request

from ..database import db
from project.models import Retailer, User


register = Blueprint("register", __name__)


@register.route("/signup", methods=["POST"])
def user_signup():
    data = request.get_json()
    user_email = data.get("email")
    user_name = data.get("name")
    user_password = data.get("password")
    hashed_password = hashpw(user_password.encode("utf-8"), gensalt())
    try:
        new_user = User(user_name, user_email, hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return f"{user_name} is registered", 200
    except Exception as e:
        return f"Error Adding", 403


@register.route("/retailer-signup", methods=["POST"])
def retailer_signup():
    try:
        data = request.get_json()
        retailer_email = data.get("email")
        retailer_name = data.get("name")
        retailer_password = data.get("password")
        hashed_password = hashpw(retailer_password.encode("utf-8"), gensalt())
        retailer_phone_number = data.get("phoneNo")
        retailer_address = data.get("address")
        new_user = Retailer(
            retailer_name,
            retailer_email,
            hashed_password,
            retailer_phone_number,
            retailer_address,
        )
        db.session.add(new_user)
        db.session.commit()
        return f"{retailer_name} is registered", 200
    except Exception as e:
        return f"Error Adding", 403
