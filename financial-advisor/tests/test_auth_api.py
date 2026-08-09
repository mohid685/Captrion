import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.db import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestRegister:
    def test_register_returns_token(self, client) -> None:
        response = client.post("/auth/register", json={"email": "test@example.com", "password": "password123"})
        assert response.status_code == 201
        assert "access_token" in response.json()

    def test_duplicate_email_rejected(self, client) -> None:
        client.post("/auth/register", json={"email": "dup@example.com", "password": "password123"})
        response = client.post("/auth/register", json={"email": "dup@example.com", "password": "password456"})
        assert response.status_code == 409

    def test_short_password_rejected(self, client) -> None:
        response = client.post("/auth/register", json={"email": "short@example.com", "password": "short"})
        assert response.status_code == 422


class TestLogin:
    def test_login_with_correct_credentials(self, client) -> None:
        client.post("/auth/register", json={"email": "login@example.com", "password": "password123"})
        response = client.post("/auth/login", json={"email": "login@example.com", "password": "password123"})
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_with_wrong_password(self, client) -> None:
        client.post("/auth/register", json={"email": "wrong@example.com", "password": "password123"})
        response = client.post("/auth/login", json={"email": "wrong@example.com", "password": "nope"})
        assert response.status_code == 401

    def test_login_with_unknown_email(self, client) -> None:
        response = client.post("/auth/login", json={"email": "ghost@example.com", "password": "password123"})
        assert response.status_code == 401


class TestProfile:
    def _register_and_get_token(self, client) -> str:
        response = client.post("/auth/register", json={"email": "profile@example.com", "password": "password123"})
        return response.json()["access_token"]

    def test_get_profile_requires_auth(self, client) -> None:
        response = client.get("/users/me/profile")
        assert response.status_code == 401

    def test_get_empty_profile(self, client) -> None:
        token = self._register_and_get_token(client)
        response = client.get("/users/me/profile", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["risk_tolerance"] is None

    def test_update_and_get_profile(self, client) -> None:
        token = self._register_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        update_response = client.put(
            "/users/me/profile",
            headers=headers,
            json={"risk_tolerance": "moderate", "investment_goals": "retirement", "preferred_sectors": "tech,healthcare"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["risk_tolerance"] == "moderate"

        get_response = client.get("/users/me/profile", headers=headers)
        assert get_response.json()["investment_goals"] == "retirement"

    def test_invalid_risk_tolerance_rejected(self, client) -> None:
        token = self._register_and_get_token(client)
        response = client.put(
            "/users/me/profile",
            headers={"Authorization": f"Bearer {token}"},
            json={"risk_tolerance": "extreme"},
        )
        assert response.status_code == 422