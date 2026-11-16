import os
import struct
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from wyltkm.core import Request, render_png, render_svg

GOLDEN = Path(__file__).parent / "golden"
NS = "{http://www.w3.org/2000/svg}"

FORTY_SCHEMES = ["green", "teal", "lavender", "lilac", "pink", "rose", "orange", "yellow",
                 "sage", "taupe", "light", "light-brown"]

CASES = {
    "attraktor-default": Request(content="https://wiki.attraktor.org/Laser", text="Laser cutter"),
    "attraktor-border-cat": Request(content="https://example.org", text="Cat", icon="fa:solid/cat",
                                    border=True),
    "attraktor-bw": Request(content="https://example.org", design="attraktor", scheme="bw",
                            text="Two\nlines"),
    "38c3-no-text": Request(content="https://events.ccc.de", design="38c3"),
    "38c3-light-carbon": Request(content="https://events.ccc.de", design="38c3", scheme="light",
                                 text="Boot", icon="carbon:boot", background=False),
    "38c3-lighter": Request(content="x", design="38c3", scheme="lighter", text="Lighter",
                            icon="none"),
    "side-up-attraktor": Request(content="https://wiki.attraktor.org/Laser", text="Laser",
                                 side=True),
    "side-long-40c3": Request(content="https://example.org/" + "/".join(["segment"] * 12),
                              design="40c3", side=True, text="Long"),
    **{f"40c3-{s}": Request(content="https://events.ccc.de/congress/2026", design="40c3",
                            scheme=s, text="Model Citizens") for s in FORTY_SCHEMES},
}


@pytest.mark.parametrize("name", sorted(CASES))
def test_golden(library, name):
    """Compare with tests/golden/<name>.svg; set UPDATE_GOLDEN=1 to rewrite."""
    svg = render_svg(library, CASES[name]).svg
    path = GOLDEN / f"{name}.svg"
    if os.environ.get("UPDATE_GOLDEN") or not path.exists():
        path.write_text(svg, encoding="utf-8")
    assert svg == path.read_text(encoding="utf-8")


@pytest.mark.parametrize("name", sorted(CASES))
def test_paths_only(library, name):
    root = ET.fromstring(render_svg(library, CASES[name]).svg.encode())
    tags = set()
    for el in root:
        if el.tag == NS + "metadata":
            continue
        tags |= {e.tag.replace(NS, "") for e in el.iter()}
        assert all(e.get("stroke") in (None, "none") for e in el.iter())
    assert tags <= {"path", "g"}


def test_deterministic(library):
    req = CASES["attraktor-border-cat"]
    assert render_svg(library, req).svg == render_svg(library, req).svg


def test_size(library):
    r = render_svg(library, Request(content="x", width=400, border=True))
    root = ET.fromstring(r.svg.encode())
    assert root.get("width") == "400"
    vb = [float(v) for v in root.get("viewBox").split()]
    assert float(root.get("height")) == pytest.approx(400 * vb[3] / vb[2], abs=0.01)


def test_layout_without_parts(library):
    """Without top text and bottom line there are no gaps: the image is square."""
    from wyltkm.core import Library
    from wyltkm.core.designs import BUILTIN_DIR, DesignRegistry
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "plain"
        d.mkdir()
        (d / "design.toml").write_text('name = "plain"\ntitle = "Plain"\n[colours]\n'
                                       'background = "#ffffff"\nmodules = "#000000"\n')
        lib = Library(DesignRegistry([Path(tmp), BUILTIN_DIR]), library.icons, library.fonts)
        root = ET.fromstring(render_svg(lib, Request(content="x", design="plain")).svg.encode())
        assert root.get("width") == root.get("height") == "250"
        assert root.get("viewBox") == "0 0 21 21"


def test_licences_and_warnings(library):
    r = render_svg(library, Request(content="x", icon="fa:solid/cat", text="Hi"))
    parts = [lic.part for lic in r.licences]
    assert parts == sorted(parts)
    assert "Design attraktor" in parts and any(p.startswith("Icons Font Awesome") for p in parts)
    assert any(lic.requires_attribution for lic in r.licence_notes)
    # Agency FB is not bundled, system fonts are off: fallback with warning
    assert any("AgencyFB-Bold.ttf" in w for w in r.warnings)
    assert "Font DejaVuSans.ttf (fallback)" in parts


def test_metadata_opt_out(library):
    with_md = render_svg(library, Request(content="x", icon="fa:solid/cat")).svg
    without = render_svg(library, Request(content="x", icon="fa:solid/cat",
                                          licence_metadata=False)).svg
    assert "<metadata>" in with_md and "CC-BY-4.0" in with_md
    assert "<metadata>" not in without


def _png_chunks(png: bytes):
    pos = 8
    while pos < len(png):
        length, kind = struct.unpack(">I4s", png[pos:pos + 8])
        yield kind, png[pos + 8:pos + 8 + length]
        pos += 12 + length


def test_png(library):
    r = render_png(library, Request(content="x", width=300, icon="fa:solid/cat"))
    assert r.png.startswith(b"\x89PNG")
    assert struct.unpack(">I", r.png[16:20])[0] == 300
    texts = [d for k, d in _png_chunks(r.png) if k == b"iTXt"]
    assert texts and b"CC-BY-4.0" in texts[0]
    r = render_png(library, Request(content="x", licence_metadata=False))
    assert not [d for k, d in _png_chunks(r.png) if k == b"iTXt"]


def test_upload(library):
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2 1"><rect width="2" height="1"/></svg>'
    r = render_svg(library, Request(content="x", icon_svg=svg))
    assert any(lic.part == "Icon (uploaded)" for lic in r.licences)
