import pytest


@pytest.mark.asyncio
async def test_homepage_status(client):
    response = await client.get("/")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_about_status(client):
    response = await client.get("/about")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_api_home_status(client):
    response = await client.get("/api")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_help_status(client):
    response = await client.get("/help")
    assert response.status_code == 200
