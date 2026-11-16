import io

import pytest
import zxingcpp
from PIL import Image

from wyltkm.core import Request, render_png
from wyltkm.core.qr import hole_size, matrix


def test_hole_size_odd_and_like_0_2_2():
    for n in range(21, 178, 4):
        size = hole_size(n)
        assert size % 2 == 1
    assert hole_size(25) == 5
    assert hole_size(33) == 9


def test_matrix_has_no_quiet_zone():
    m = matrix("x")
    assert len(m) == 21 and all(m[0][:7])


def _decode(png: bytes, background: str) -> list[str]:
    im = Image.open(io.BytesIO(png)).convert("RGB")
    rgb = tuple(int(background[i:i + 2], 16) for i in (1, 3, 5))
    canvas = Image.new("RGB", (im.width + 100, im.height + 100), rgb)
    canvas.paste(im, (50, 50))
    return [r.text for r in zxingcpp.read_barcodes(canvas)]


CONTENTS = ["x", "https://wiki.attraktor.org/Laser", "https://example.org/" + "a" * 150,
            "Hällo Wörld"]


@pytest.mark.parametrize("design", ["attraktor", "attraktor-bw", "38c3", "38c3-light",
                                    "38c3-lighter"])
@pytest.mark.parametrize("icon", ["none", "fa:solid/cat"])
def test_codes_decode(library, design, icon):
    bg = library.design(design).colours()["background"]
    for content in CONTENTS:
        r = render_png(library, Request(content=content, design=design, icon=icon, width=500,
                                        text="Test"))
        assert content in _decode(r.png, bg), (design, icon, content)
