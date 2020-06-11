from declaraciones_feuc.declaraciones import app

import pytest


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_http(client):
    """Tests whether there is a 403 http response on root"""

    response = client.get("/")
    assert response.status_code == 200


def test_http_statements(client):
    """Tests whether there is a 200 http response on statements"""

    response = client.get("/declaraciones")
    assert response.status_code == 200


def test_http_representatives(client):
    """Tests whether there is a 200 http response on representatives"""

    response = client.get("/representantes")
    assert response.status_code == 200


def test_settings_forbidden(client):
    """Tests whether there is a 403 http response on settings"""

    response = client.get("/ajustes")
    assert response.status_code == 403


def test_members_forbidden(client):
    """Tests whether there is a 403 http response on members"""

    response = client.get("/miembros")
    assert response.status_code == 403


def test_org_forbidden(client):
    """Tests whether there is a 403 http response on org"""

    response = client.get("/org")
    assert response.status_code == 403
