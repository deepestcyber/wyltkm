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
    assert data["attraktor"]["default"] and data["attraktor"]["default_scheme"] == "colour"
    assert [s["icon"] for s in data["attraktor"]["schemes"]] == ["attraktor:logo",
                                                                  "attraktor:logo-mono"]
    forty = data["40c3"]
    assert forty["default_scheme"] == "green" and len(forty["schemes"]) == 12
    r = client.get(forty["schemes"][4]["preview"])
    assert r.status_code == 200 and r.mimetype == "image/svg+xml" and b"#eb5d9d" in r.data
    assert client.get(data["38c3"]["preview"]).status_code == 200
    assert client.get("/designs/nope/preview.svg").status_code == 404
    assert client.get("/designs/40c3/preview.svg?scheme=nope").status_code == 400
    assert client.get("/designs/attraktor/preview.svg?scheme=x").status_code == 400
    assert client.get("/designs/38c3/preview.svg?scheme=x").status_code == 400


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
    r = client.get("/?icon=carbon:boot")
    assert b'value="carbon:boot" checked' in r.data


def test_render_info(client):
    info = client.get("/api/render-info?content=x&icon=fa:solid/cat&side=1").get_json()
    assert info["width"] == 250 and info["modules"] == 21 and info["height"] > 250
    assert any(lic["requires_attribution"] for lic in info["licences"])
    assert client.get("/api/render-info?content=x&design=nope").status_code == 404
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><path d="M0 0H1V1Z"/></svg>'
    r = client.post("/api/render-info", data={"content": "x", "icon_file": (io.BytesIO(svg), "i.svg")},
                    content_type="multipart/form-data")
    assert any(lic["part"] == "Icon (uploaded)" for lic in r.get_json()["licences"])


def test_caching(client):
    for url in ("/render.svg?content=x", "/render.png?content=x", "/designs/40c3/preview.svg",
                "/icons/fa/solid/cat.svg"):
        r = client.get(url)
        assert r.status_code == 200 and r.headers["ETag"] and r.cache_control.max_age
        again = client.get(url, headers={"If-None-Match": r.headers["ETag"]})
        assert again.status_code == 304, url


def test_ui_fonts_and_pages(client):
    assert client.get("/ui-fonts/SpaceGrotesk-Regular.otf").status_code == 200
    assert client.get("/ui-fonts/Pilowlava-Regular.otf").status_code == 404
    assert client.get("/ui-fonts/..%2F..%2Fx").status_code == 404
    page = client.get("/").data
    assert b"app.js" in page and b'id="preview"' in page and b"Download SVG" in page
    assert b"Font Awesome" in client.get("/licences").data
    assert b"Printing and laser cutting" in client.get("/help").data
    names = [d["name"] for d in client.get("/api/designs").get_json()]
    assert names[0] == "attraktor"


def test_icon_browser(client):
    data = client.get("/api/icons/browse?source=fa&folder=brands&limit=5").get_json()
    assert data["offset"] == 0 and data["total"] > 500 and len(data["hits"]) == 5
    page2 = client.get("/api/icons/browse?source=fa&folder=brands&limit=5&offset=5").get_json()
    assert not {h["name"] for h in data["hits"]} & {h["name"] for h in page2["hits"]}
    assert client.get("/api/icons/browse?offset=x").status_code == 400
    assert client.get("/api/icons/browse?source=nope").status_code == 404
    sources = {s["name"]: s for s in client.get("/api/icon-sources").get_json()}
    assert {f["name"] for f in sources["40c3"]["folders"]} == {"citizens", "icons-deco", "logos"}
    r = client.get("/icons/browse?source=40c3&folder=logos&design=40c3&text=Hi")
    assert r.status_code == 200 and r.data.count(b'class="icon"') == 28
    assert b"/?design=40c3&amp;text=Hi&amp;icon=40c3%3Alogos" in r.data
    assert b'id="browser"' in client.get("/").data
