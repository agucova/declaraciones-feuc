from declaraciones_feuc.declaraciones import app

import pytest


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_http(client):  # TODO: #8 Añadir tests reales
    """Tests whether there is a 200 http response on root"""

    response = client.get("/")
    assert response.status_code == 200
