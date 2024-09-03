from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel

from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config

APP = Flask(__name__)
APP.config.from_object(Config)
APP.wsgi_app = ProxyFix(APP.wsgi_app)

from glyfy.models import Base  # noqa: E402

DB = SQLAlchemy(APP, model_class=Base)
babel = Babel(APP)

# circular
from glyfy.routes import USER_BP  # noqa: E402
from glyfy.admin_routes import ADMIN_BP  # noqa: E402

APP.register_blueprint(USER_BP)
APP.register_blueprint(ADMIN_BP)
