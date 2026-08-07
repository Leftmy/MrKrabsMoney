# tests/conftest.py
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import scoped_session, sessionmaker
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
    return _app


@pytest.fixture(autouse=True)
def app_context(app):
    """Pushes app context for every test automatically."""
    with app.app_context():
        yield


@pytest.fixture(scope="session")
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture(autouse=True)
def db_session(db):
    """
    Creates a new database transaction for each test and rolls back 
    after completion to ensure complete test isolation.
    """
    connection = db.engine.connect()
    transaction = connection.begin()

    Session = scoped_session(sessionmaker(bind=connection))
    db.session = Session

    yield Session

    Session.remove()
    transaction.rollback()
    connection.close()

@pytest.fixture
def mock_stripe_payment_intent():
    """Mocks stripe.PaymentIntent.create API call and returns a fake intent object."""
    with patch("stripe.PaymentIntent.create") as mock_create:
        fake_intent = MagicMock()
        fake_intent.id = "pi_test_123456789"
        fake_intent.status = "succeeded"
        mock_create.return_value = fake_intent
        yield mock_create