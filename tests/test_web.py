import io

import pytest

from wyltkm.web import create_app


@pytest.fixture()
def client(library):
    return create_app(library).test_client()


def test_pages(client):
    for url in ("/", "/?design=38c3&text=Hi", "/help", "/licences"):
        assert client.get(url).status_code == 200
    assert b"unknown design" in client.get("/?design=nope").data


def test_render(client):
    r = client.get("/render.svg?content=x&text=Hello%20World&download=1")
    assert r.status_code == 200 and r.mimetype == "image/svg+xml"
    assert "hello-world.svg" in r.headers["Content-Disposition"]
    r = client.get("/render.png?content=x")
    assert r.mimetype == "image/png"


@pytest.mark.parametrize("query, status", [
    ("content=x&icon=fa:solid/nope", 404),
    ("content=x&design=nope", 404),
    ("content=x&width=99999", 400),
    ("content=x&border=2", 400),
    ("content=x&scheme=main", 400),
    ("content=", 400),
])
def test_errors(client, query, status):
    assert client.get(f"/render.svg?{query}").status_code == status


def test_upload(client):
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><path d="M0 0H1V1Z"/></svg>'
    r = client.post("/render.svg", data={"content": "x", "icon_file": (io.BytesIO(svg), "i.svg")},
                    content_type="multipart/form-data")
    assert r.status_code == 200
    r = client.post("/render.svg", data={"content": "x", "icon": "fa:solid/cat",
                                         "icon_file": (io.BytesIO(svg), "i.svg")},
                    content_type="multipart/form-data")
    assert r.status_code == 400


def test_api_licences(client):
    data = client.get("/api/licences?content=x&icon=fa:solid/cat").get_json()
    assert any(lic["requires_attribution"] for lic in data)
