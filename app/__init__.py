from flask import Flask
from flask_migrate import Migrate

from app.config import Config
from app.extensions import db
from app.api.v1.payment_controller import payment_bp
from app.api.v1.webhook_controller import webhook_bp

migrate = Migrate()

def create_app(config_override=None):
    app = Flask(__name__)

    app.config.from_object(Config)

    if config_override:
        app.config.update(config_override)

    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(payment_bp)
    app.register_blueprint(webhook_bp)

    return app