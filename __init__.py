from flask import Flask
from flask_cors import CORS

from .database import db, jwt
from .routes import main
from .modules.product_upload import upload
from .modules.order_input import orderInput
from .modules.register_page import register
from .modules.login_module import login
from .modules.stats_generation import statics
from .modules.view_profile import viewProfile
from .modules.update_profile import updateProfile
from .modules.search_results import searchResults
from .modules.product_inventory import productInventory
from .modules.registration_confirmation import registrationConfirmation
from .modules.order_preview import orderPreview
from .modules.admin_home import adminHome
from .modules.past_orders import pastOrders


def create_app(database_uri="mysql://root:@localhost/dev"):
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/dev"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["UPLOAD_FOLDER"] = "uploads"
    app.config["JWT_SECRET_KEY"] = "please-remember-to-change-me"
    app.config["SECRET_KEY"] = "Vivek Kum"

    db.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(main)
    app.register_blueprint(orderInput, name="orderInput")
    app.register_blueprint(upload, name="productUpload")
    app.register_blueprint(register, name="register")
    app.register_blueprint(login, name="login")
    app.register_blueprint(statics, name="statics")
    app.register_blueprint(viewProfile, name="viewProfile")
    app.register_blueprint(updateProfile, name="updateProfile")
    app.register_blueprint(searchResults, name="searchResults")
    app.register_blueprint(productInventory, name="productInventory")
    app.register_blueprint(registrationConfirmation, name="registrationConfirmation")
    app.register_blueprint(orderPreview, name="orderPreview")
    app.register_blueprint(adminHome, name="adminHome")
    app.register_blueprint(pastOrders, name="pastOrders")

    return app
