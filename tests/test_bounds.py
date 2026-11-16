import pytest

from wyltkm.core.bounds import ink_box, parse_transform, path_points
from wyltkm.core.svg import normalise


def _box(d):
    pts = path_points(d)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


@pytest.mark.parametrize("d, expected", [
    ("M10 10H20V30H10Z", (10, 10, 20, 30)),
    ("M10 10h10v20h-10z", (10, 10, 20, 30)),
    ("M0 0L1 1 2 0", (0, 0, 2, 1)),                    # implicit line-tos after M
    ("M292.7-4.7l64 64", (292.7, -4.7, 356.7, 59.3)),   # compact numbers, FA style
    ("M0 5A5 5 0 0 1 10 5", (0, 0, 10, 5)),            # half circle bulging up
    ("M0 5a5 5 0 011 0", (0, 4.975, 1, 5)),             # flags without separators
])
def test_path_points(d, expected):
    assert _box(d) == pytest.approx(expected, abs=0.01)


def test_curves_are_tight():
    # control points reach y=-100, the curve itself only y=-75
    lo = _box("M0 0C0 -100 100 -100 100 0")[1]
    assert lo == pytest.approx(-75, abs=0.5)
    # smooth curve reflects the previous control point
    assert _box("M0 0C0 -10 10 -10 10 0S20 10 20 0")[3] == pytest.approx(7.5, abs=0.5)


def test_transforms():
    assert parse_transform("translate(10 20) scale(2)") == pytest.approx((2, 0, 0, 2, 10, 20))
    n = normalise(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                  b'<g transform="translate(5 0)"><path d="M0 0H10V10H0Z"/></g></svg>')
    assert n.ink == pytest.approx((5, 0, 10, 10))
    assert n.box == pytest.approx((0, 0, 15, 10))  # viewBox grown to the ink


def test_invisible_shapes_do_not_count():
    n = normalise(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                  b'<rect x="-50" y="-50" width="200" height="200" fill="none"/>'
                  b'<path d="M2 2H8V8H2Z"/></svg>')
    assert n.ink == pytest.approx((2, 2, 6, 6)) and n.box == (0, 0, 10, 10)


def test_overflowing_icon_is_placed_inside(library):
    """fa:solid/elevator draws above its viewBox; the box must contain it."""
    _, n = library.icon("fa:solid/elevator", "#000000")
    assert n.viewbox == (0, 0, 512, 512)
    bx, by, bw, bh = n.box
    ix, iy, iw, ih = n.ink
    assert by < 0 and bx <= ix and by <= iy and bx + bw >= ix + iw and by + bh >= iy + ih


def test_icon_svg_shows_everything(library):
    from wyltkm.core import render_icon
    svg = render_icon(library, "fa:solid/elevator")
    assert 'viewBox="0 -32 512 544"' in svg
