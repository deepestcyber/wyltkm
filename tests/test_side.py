import io
import xml.etree.ElementTree as ET

import pytest
import ziafont
import zxingcpp
from PIL import Image

from wyltkm.core import InvalidRequest, Request, render_png, render_svg
from wyltkm.core import side as sidemod
from wyltkm.core.fonts import BUNDLED_DIR

NS = "{http://www.w3.org/2000/svg}"
HACK = ziafont.Font(str(BUNDLED_DIR / "Hack-Regular.ttf"))


def test_pieces_break_after_characters():
    assert sidemod._pieces("https://a.b/c?d=1&e") == [
        "https:/", "/", "a.", "b/", "c?", "d=", "1&", "e"]


def test_short_content_one_column():
    lay = sidemod.layout(HACK, "https://example.org", 40, 1.5, 3, 4)
    assert lay.columns == ["https://example.org"] and lay.warning is None


def test_long_content_wraps_balanced_at_break_characters():
    content = "https://example.org/" + "/".join(["segment"] * 10)
    lay = sidemod.layout(HACK, content, 40, 1.5, 3, 4)
    assert 1 < len(lay.columns) <= 4
    assert "".join(lay.columns) == content
    assert all(c.endswith("/") for c in lay.columns[:-1])  # soft breaks only
    widths = [sidemod.textmod.ink_width(HACK, c) for c in lay.columns]
    assert max(widths) * lay.scale <= 40 + 1e-6
    cap = sidemod.textmod.cap_height(HACK)
    assert cap * lay.scale >= 1.5


def test_line_breaks_are_kept():
    lay = sidemod.layout(HACK, "first line\nsecond", 40, 1.5, 3, 4)
    assert lay.columns == ["first line", "second"]


def test_too_long_gets_smaller_with_warning():
    lay = sidemod.layout(HACK, "x" * 400, 20, 1.5, 3, 2)
    assert len(lay.columns) == 2 and lay.warning
    assert sidemod.textmod.cap_height(HACK) * lay.scale < 1.5


def test_max_size():
    lay = sidemod.layout(HACK, "x", 40, 1.5, 3, 4)
    assert sidemod.textmod.cap_height(HACK) * lay.scale == pytest.approx(3)


def _size(svg):
    root = ET.fromstring(svg.encode())
    return [float(v) for v in root.get("viewBox").split()]


@pytest.mark.parametrize("design", ["attraktor", "40c3"])
def test_render_with_side_text(library, design):
    plain = render_svg(library, Request(content="https://example.org", design=design))
    side = render_svg(library, Request(content="https://example.org", design=design, side=True))
    pw, ph = _size(plain.svg)[2:]
    sw, sh = _size(side.svg)[2:]
    assert sw > pw and sh == ph
    assert "Font Hack-Regular.ttf" in [lic.part for lic in side.licences]
    assert 'rotate(-90)' in side.svg


def test_direction_and_font(library, tmp_path):
    from wyltkm.core import Library
    from wyltkm.core.designs import BUILTIN_DIR, DesignRegistry
    d = tmp_path / "down"
    d.mkdir()
    (d / "design.toml").write_text('name = "down"\ntitle = "Down"\nextends = "38c3"\n'
                                   '[side]\ndirection = "down"\n')
    lib = Library(DesignRegistry([tmp_path, BUILTIN_DIR]), library.icons, library.fonts)
    r = render_svg(lib, Request(content="x", design="down", side=True,
                                side_font="SpaceGrotesk-Regular.otf"))
    assert "rotate(90)" in r.svg
    assert "Font SpaceGrotesk-Regular.otf" in [lic.part for lic in r.licences]
    with pytest.raises(InvalidRequest):
        render_svg(lib, Request(content="x", side=True, side_font="Nope.ttf"))
    with pytest.raises(InvalidRequest):
        Request(content="x", side_font="../x.ttf")


@pytest.mark.parametrize("content", ["https://example.org",
                                     "https://example.org/" + "/".join(["abc"] * 30)])
def test_still_scans(library, content):
    r = render_png(library, Request(content=content, design="40c3", side=True, width=700,
                                    border=True))
    im = Image.open(io.BytesIO(r.png)).convert("RGB")
    assert content in [x.text for x in zxingcpp.read_barcodes(im)]
