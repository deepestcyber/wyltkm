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


def test_api_designs_and_previews(client):
    data = {d["name"]: d for d in client.get("/api/designs").get_json()}
    assert data["attraktor"]["default"] and data["attraktor"]["schemes"] == []
    forty = data["40c3"]
    assert forty["default_scheme"] == "green" and len(forty["schemes"]) == 12
    r = client.get(forty["schemes"][4]["preview"])
    assert r.status_code == 200 and r.mimetype == "image/svg+xml" and b"#eb5d9d" in r.data
    assert client.get(data["38c3"]["preview"]).status_code == 200
    assert client.get("/designs/nope/preview.svg").status_code == 404
    assert client.get("/designs/40c3/preview.svg?scheme=nope").status_code == 400
    assert client.get("/designs/attraktor/preview.svg?scheme=x").status_code == 400


def test_api_licences(client):
    data = client.get("/api/licences?content=x&icon=fa:solid/cat").get_json()
    assert any(lic["requires_attribution"] for lic in data)


def test_limits_from_config(tmp_path, monkeypatch):
    from wyltkm.core import Library
    conf = tmp_path / "c.toml"
    conf.write_text("[web]\nmax_width = 300\nmax_upload_bytes = 100\n")
    monkeypatch.setenv("WYLTKM_CONFIG", str(conf))
    client = create_app(Library.from_config()).test_client()
    assert client.get("/render.svg?content=x&width=301").status_code == 400
    assert client.get("/render.svg?content=x&width=300").status_code == 200
    big = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">' + b" " * 200 + b"</svg>"
    r = client.post("/render.svg", data={"content": "x", "icon_file": (io.BytesIO(big), "i.svg")},
                    content_type="multipart/form-data")
    assert r.status_code == 400 and b"larger" in r.data


def test_icons_api_and_route(client):
    hits = client.get("/api/icons?q=github&limit=2").get_json()
    assert [h["name"] for h in hits] == ["fa:brands/github", "fa:brands/github-alt"]
    assert client.get(hits[0]["url"]).status_code == 200
    r = client.get("/icons/carbon/boot.svg?colour=%23123456")
    assert r.status_code == 200 and b"#123456" in r.data
    assert client.get("/icons/fa/solid/nope.svg").status_code == 404
    assert client.get("/icons/fa/solid/cat.svg?colour=red").status_code == 400
    assert client.get("/api/icons?limit=x").status_code == 400
    sources = {s["name"] for s in client.get("/api/icon-sources").get_json()}
    assert {"fa", "carbon", "40c3"} <= sources


def test_side_text(client):
    r = client.get("/render.svg?content=x&side=1&side_font=Hack-Regular.ttf")
    assert r.status_code == 200 and b"rotate(-90)" in r.data
    assert client.get("/render.svg?content=x&side=1&side_font=No.ttf").status_code == 400
    assert client.get("/render.svg?content=x&side=2").status_code == 400
    fonts = [f["name"] for f in client.get("/api/fonts").get_json()]
    assert "Hack-Regular.ttf" in fonts and "jersey-10-latin-400-normal.ttf" in fonts
    assert b'name="side_font"' in client.get("/").data


def test_icon_search_in_form(client):
    r = client.get("/?icon_q=cat")
    assert r.status_code == 200 and b'value="fa:solid/cat"' in r.data
    r = client.get("/?icon=fa:solid/cat&icon=carbon:boot")
    assert b'value="carbon:boot"' in r.data
