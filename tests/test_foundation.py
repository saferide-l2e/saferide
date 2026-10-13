from django.test import Client


def test_home_loads():
    response = Client().get("/")
    assert response.status_code == 200
    assert b"SafeRide" in response.content


def test_health_is_minimal():
    response = Client().get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
