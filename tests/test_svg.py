import pytest

from wyltkm.core import DataError, InvalidRequest
from wyltkm.core.svg import normalise


def _tags(n):
    return {el.tag for el in n.group.iter()}


def test_primitives_become_paths():
    n = normalise(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                  b'<rect x="1" y="1" width="4" height="4" rx="1"/><circle cx="5" cy="5" r="2"/>'
                  b'<ellipse cx="5" cy="5" rx="2" ry="1"/><polygon points="0,0 1,0 1,1"/>'
                  b'<line x1="0" y1="0" x2="1" y2="1" stroke="red"/></svg>')
    assert _tags(n) == {"g", "path"}
    assert n.viewbox == (0, 0, 10, 10)
    assert any("strokes" in w for w in n.warnings)


def test_recolour_keeps_invisible_shapes_invisible():
    n = normalise(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
                  b'<defs><style>.cls-1 { fill: none; }</style></defs>'
                  b'<path d="M0 0H1V1Z"/><rect class="cls-1" width="32" height="32"/></svg>',
                  recolour="#123456")
    fills = [el.get("fill") for el in n.group.iter("path")]
    assert fills == ["#123456", "none"]


def test_styles_resolved_and_classes_dropped():
    n = normalise(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">'
                  b'<style>.a{fill:#ff0000}</style><g style="opacity:0.5">'
                  b'<path class="a" d="M0 0H1V1Z" onclick="evil()"/></g></svg>')
    path = next(n.group.iter("path"))
    assert path.get("fill") == "#ff0000"
    assert path.get("class") is None and path.get("onclick") is None


def test_unsafe_content_removed():
    n = normalise(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">'
                  b'<script>alert(1)</script><foreignObject/><image href="http://x"/>'
                  b'<path d="M0 0H1V1Z"/></svg>')
    assert _tags(n) == {"g", "path"}


def test_ids_prefixed_and_clip_warned():
    n = normalise(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">'
                  b'<clipPath id="c"><rect width="1" height="1"/></clipPath>'
                  b'<path clip-path="url(#c)" d="M0 0H1V1Z"/></svg>', id_prefix="icon-")
    assert {el.get("id") for el in n.group.iter("clipPath")} == {"icon-c"}
    assert any(el.get("clip-path") == "url(#icon-c)" for el in n.group.iter("path"))
    assert any("clip paths" in w for w in n.warnings)


@pytest.mark.parametrize("data", [
    b'<!DOCTYPE svg [<!ENTITY a "b">]><svg>&a;</svg>',
    b'<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0"/></svg>',  # no viewBox
    b'<html/>',
    b'not xml',
    b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"></svg>',
])
def test_hostile_or_broken_upload(data):
    with pytest.raises(InvalidRequest):
        normalise(data, untrusted=True)
    with pytest.raises(DataError):
        normalise(data)


def test_limits():
    many = b"".join(b'<path d="M0 0H1V1Z"/>' for _ in range(50))
    with pytest.raises(InvalidRequest, match="elements"):
        normalise(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">' + many + b"</svg>",
                  untrusted=True, max_elements=20)
    deep = b"<g>" * 30 + b'<path d="M0 0H1V1Z"/>' + b"</g>" * 30
    with pytest.raises(InvalidRequest, match="deeper"):
        normalise(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1">' + deep + b"</svg>",
                  untrusted=True, max_depth=20)
