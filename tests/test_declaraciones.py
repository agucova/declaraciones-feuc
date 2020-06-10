from declaraciones_feuc import declaraciones

import pytest
import tempfile
import os


@pytest.fixture
def client():
    db_fd, declaraciones.app.config["DATABASE"] = tempfile.mkstemp()
    declaraciones.app.config["TESTING"] = True

    with declaraciones.app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(declaraciones.app.config["DATABASE"])


def test_http(client):
    """Tests whether there is a 200 http response on root"""

    response = client.get("/")
    assert response.status_code == 200
