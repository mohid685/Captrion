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


@pytest.fixture
def auth_headers(client):
    response = client.post("/auth/register", json={"email": "mem@example.com", "password": "password123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestWatchlist:
    def test_add_and_list(self, client, auth_headers) -> None:
        add_response = client.post("/users/me/watchlist", headers=auth_headers, json={"ticker": "aapl"})
        assert add_response.status_code == 201
        assert add_response.json()["ticker"] == "AAPL"

        list_response = client.get("/users/me/watchlist", headers=auth_headers)
        assert len(list_response.json()) == 1

    def test_duplicate_rejected(self, client, auth_headers) -> None:
        client.post("/users/me/watchlist", headers=auth_headers, json={"ticker": "TSLA"})
        response = client.post("/users/me/watchlist", headers=auth_headers, json={"ticker": "TSLA"})
        assert response.status_code == 409

    def test_delete(self, client, auth_headers) -> None:
        client.post("/users/me/watchlist", headers=auth_headers, json={"ticker": "MSFT"})
        delete_response = client.delete("/users/me/watchlist/MSFT", headers=auth_headers)
        assert delete_response.status_code == 204
        assert client.get("/users/me/watchlist", headers=auth_headers).json() == []

    def test_requires_auth(self, client) -> None:
        response = client.get("/users/me/watchlist")
        assert response.status_code == 401


class TestPortfolio:
    def test_add_and_list(self, client, auth_headers) -> None:
        response = client.post(
            "/users/me/portfolio", headers=auth_headers, json={"ticker": "aapl", "shares": 10, "cost_basis": 280.50}
        )
        assert response.status_code == 201
        assert response.json()["ticker"] == "AAPL"
        assert response.json()["shares"] == 10

    def test_negative_shares_rejected(self, client, auth_headers) -> None:
        response = client.post(
            "/users/me/portfolio", headers=auth_headers, json={"ticker": "AAPL", "shares": -5, "cost_basis": 100}
        )
        assert response.status_code == 422

    def test_delete(self, client, auth_headers) -> None:
        client.post("/users/me/portfolio", headers=auth_headers, json={"ticker": "GOOG", "shares": 5, "cost_basis": 150})
        delete_response = client.delete("/users/me/portfolio/GOOG", headers=auth_headers)
        assert delete_response.status_code == 204


class TestConversations:
    def test_empty_history(self, client, auth_headers) -> None:
        response = client.get("/users/me/conversations", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []