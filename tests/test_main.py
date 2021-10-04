from starlette.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_homepage_status():
    response = client.get("/")
    assert response.status_code == 200


def test_about_status():
    response = client.get("/about")
    assert response.status_code == 200


def test_api_home_status():
    response = client.get("/api")
    assert response.status_code == 200


def test_help_status():
    response = client.get("/help")
    assert response.status_code == 200
