from starlette.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_homepage_status():
    response = client.get("/")
    assert response.status_code == 200


def test_about_status():
    response = client.get("/about")
    assert response.status_code == 200
