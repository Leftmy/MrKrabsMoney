import pytest
from unittest.mock import patch, MagicMock
from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    _app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "CELERY_TASK_ALWAYS_EAGER": True,
        "CELERY_TASK_EAGER_PROPAGATION": True,
        "STRIPE_SECRET_KEY": "sk_test_fake_key",
        "STRIPE_WEBHOOK_SECRET": "whsec_fake_secret",
    })

    with _app.app_context():
        yield _app


@pytest.fixture(scope="session")
def db(app):
    _db.create_all()
    yield _db
    _db.drop_all()


@pytest.fixture(scope="function", autouse=True)
def db_session(db):
    connection = db.engine.connect()
    transaction = connection.begin()
    
    session = db.create_scoped_session(options={"bind": connection})
    db.session = session

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_stripe_payment_intent():
    with patch("stripe.PaymentIntent.create") as mock_create:
        mock_intent = MagicMock()
        mock_intent.id = "pi_test_123456789"
        mock_intent.status = "succeeded"
        mock_intent.amount = 1515
        mock_intent.currency = "usd"
        mock_create.return_value = mock_intent
        yield mock_create


@pytest.fixture
def mock_stripe_webhook_verify():
    with patch("stripe.Webhook.construct_event") as mock_verify:
        mock_verify.return_value = {
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "id": "pi_test_123456789",
                    "status": "succeeded",
                    "amount": 1515,
                    "currency": "usd"
                }
            }
        }
        yield mock_verify