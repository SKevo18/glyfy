from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel

from config import Config

db = SQLAlchemy()
babel = Babel()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    babel.init_app(app)

    from app.routes import bp
    from app.admin_routes import admin_bp

    app.register_blueprint(bp)
    app.register_blueprint(admin_bp)

    return app
