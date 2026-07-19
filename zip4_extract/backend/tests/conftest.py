"""
Shared pytest fixtures: an isolated in-memory SQLite DB per test session,
a seeded Founder user, and a FastAPI TestClient with the DB dependency
overridden so tests never touch the real backend/data/*.db file.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db.base_class import Base
from app.db.session import get_db
from app.core.security import hash_password
from app.main import app
from app import models  # noqa: F401
from app.models.identity import Role, Permission, User
from app.models.vertical import BusinessVertical

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # single shared connection -- required so the
                            # TestClient's request thread sees the same
                            # in-memory DB as the fixtures that seed it
)
TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def _fresh_schema():
    """Recreate all tables before every test function. Required because
    StaticPool gives every test the same physical in-memory connection
    (see engine comment above) -- without this, data from one test (e.g.
    a 'Founder' role or a user email) would collide with the next test's
    fixtures via unique constraints."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def founder_token(client, db_session):
    role = Role(name="Founder", is_system_role=True)
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)

    user = User(email="founder@test.com", hashed_password=hash_password("Test1234!"),
                full_name="Test Founder", role_id=role.id, is_active=True)
    db_session.add(user)
    db_session.commit()

    resp = client.post("/api/v1/auth/login", json={"email": "founder@test.com", "password": "Test1234!"})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture()
def vertical_id(client, db_session, founder_token):
    v = BusinessVertical(name="Test Vertical", slug="test-vertical",
                          pipeline_stages=["New", "Contacted", "Won", "Lost"])
    db_session.add(v)
    db_session.commit()
    db_session.refresh(v)
    return v.id
