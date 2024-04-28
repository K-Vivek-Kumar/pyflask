from flask import Flask
from flask_cors import CORS

from .database import db, jwt
from .routes import main
from .modules.product_upload import upload


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

    app.register_blueprint(main)
    app.register_blueprint(upload)

    return app
