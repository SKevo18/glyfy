from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel

from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
babel = Babel(app)

# circular
from glyfy.routes import bp  # noqa: E402
from glyfy.admin_routes import admin_bp  # noqa: E402

app.register_blueprint(bp)
app.register_blueprint(admin_bp)
