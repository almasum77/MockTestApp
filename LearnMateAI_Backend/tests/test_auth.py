import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app, get_db
from src.database.models import Base, User
from src.database.schemas import UserCreate
from unittest.mock import MagicMock, patch

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # Use SQLite in-memory for tests

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="module")
def test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def client():
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

def test_signup(client):
    response = client.post("/signup/", json={
        "email": "testuser@example.com",
        "password": "testpassword",
        "firstname": "Test",
        "lastname": "User"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"

def test_login(client, test_db):
    # First, create a user
    user = User(
        email="testuser@example.com",
        hashedpassword="$2b$12$KIXkXJLmgwYxE2M03kGH..X8/n3pkdz9Q3zQEDWoc9jQ.8q0IbuaW",  # bcrypt hash for "testpassword"
        firstname="Test",
        lastname="User"
    )
    test_db.add(user)
    test_db.commit()

    response = client.post("/login/", json={"email": "testuser@example.com", "password": "testpassword"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
