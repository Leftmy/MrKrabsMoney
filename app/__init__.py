from flask import Flask
from app.config import Config
from app.extensions import db
from app.api.v1.payment_controller import payment_bp


def create_app(config_override=None):
    app = Flask(__name__)

    app.config.from_object(Config)

    if config_override:
        app.config.update(config_override)

    db.init_app(app)

    app.register_blueprint(payment_bp)

    return app