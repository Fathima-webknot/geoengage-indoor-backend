import os
from collections.abc import Generator
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Use test DB URL if set, else same as app (tests will roll back)
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", settings.database_url)

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def mock_firebase_user():
    return {"uid": "test-firebase-uid", "email": "test@example.com", "name": "Test User"}


@pytest.fixture
def client(db: Session, mock_firebase_user: dict):
    from app.db.models import User

    # Create test user in DB so get_or_create_user finds them
    user = User(
        firebase_uid=mock_firebase_user["uid"],
        email=mock_firebase_user["email"],
        name=mock_firebase_user["name"],
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    def _get_db_override():
        yield db

    app.dependency_overrides[get_db] = _get_db_override
    with patch("app.api.deps.verify_id_token", return_value=mock_firebase_user):
        yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(db: Session, mock_firebase_user: dict):
    from app.db.models import User

    admin = User(
        firebase_uid="admin-firebase-uid",
        email="admin@example.com",
        name="Admin User",
        role="admin",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    def _get_db_override():
        yield db

    app.dependency_overrides[get_db] = _get_db_override
    with patch("app.api.deps.verify_id_token", return_value={
        "uid": "admin-firebase-uid",
        "email": "admin@example.com",
        "name": "Admin User",
    }):
        yield TestClient(app)
    app.dependency_overrides.clear()
