from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_hello_world():
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}

