import pytest

@pytest.mark.asyncio
async def test_register_and_login(client):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone": "+380000000000",
        "password": "password123",
        "birth_date": "2000-01-01T00:00:00"
    }

    r = await client.post("/auth/register/client", json=payload)
    assert r.status_code == 201
    token = r.json()["access_token"]
    assert token

    login_data = {
        "email": payload["email"],
        "password": payload["password"]
    }
    r2 = await client.post("/auth/login", json=login_data)
    assert r2.status_code == 200
    assert "access_token" in r2.json()
