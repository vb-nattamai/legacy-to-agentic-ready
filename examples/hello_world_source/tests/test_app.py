"""Tests for hello_world Flask API."""
import pytest
import app as app_module
from app import app


@pytest.fixture(autouse=True)
def clear_greetings():
    """Reset in-memory store before each test."""
    app_module._greetings.clear()
    yield


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_index_returns_service_name(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["service"] == "hello_world"
    assert "version" in data


def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_greet_returns_personalised_message(client):
    resp = client.get("/greet/Alice")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["name"] == "Alice"
    assert "Alice" in data["message"]


def test_greetings_list_grows(client):
    client.get("/greet/Alice")
    client.get("/greet/Bob")
    resp = client.get("/greetings")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
