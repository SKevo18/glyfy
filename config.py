import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "abc123")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///glyfy.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BABEL_DEFAULT_LOCALE = "en"
    BABEL_SUPPORTED_LOCALES = ["en", "sk"]
