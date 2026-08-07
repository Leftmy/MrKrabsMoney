# app/__init__.py
from flask import Flask
from app.extensions import db


def create_app(config_override=None):
    app = Flask(__name__)
    
    if config_override:
        app.config.update(config_override)

    db.init_app(app)

    return app