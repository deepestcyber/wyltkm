import pytest

from wyltkm.core import InvalidRequest, Request


def test_defaults():
    r = Request(content="https://example.org")
    assert r.width == 250 and r.design is None and r.border is None
    assert r.licence_metadata is True


@pytest.mark.parametrize("kwargs", [
    {"content": ""},
    {"content": "x", "width": 49},
    {"content": "x", "width": 10001},
    {"content": "x", "width": True},
    {"content": "x", "design": "Bad Name"},
    {"content": "x", "scheme": "../x"},
    {"content": "x", "icon": "cat"},
    {"content": "x", "icon": "fa:../cat"},
    {"content": "x", "icon": "fa:solid//cat"},
    {"content": "x", "icon": "fa:solid/cat", "icon_svg": b"<svg/>"},
    {"content": "x" * 3000},
])
def test_invalid(kwargs):
    with pytest.raises(InvalidRequest):
        Request(**kwargs)


def test_icon_names():
    Request(content="x", icon="none")
    Request(content="x", icon="carbon:drone--front")
    Request(content="x", icon="fa:solid/cat")


def test_lines():
    assert Request(content="x", text="\nA\r\nB\n\n").lines == ["A", "B"]
    assert Request(content="x").lines == []
