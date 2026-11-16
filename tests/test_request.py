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


def test_markers_in_top_and_bottom_text():
    from wyltkm.core.text import Run
    r = Request(content="x", text="Laser [cutter]\na [[b]]", bottom="SCAN [ME]")
    assert r.top_runs == [[Run("Laser "), Run("cutter", True)], [Run("a [b]")]]
    assert r.bottom_runs == [[Run("SCAN "), Run("ME", True)]]
    assert Request(content="x").bottom_runs is None
    assert Request(content="x", bottom="").bottom_runs == []
    assert Request(content="x", bottom="\n  \n").bottom_runs == []
    for kwargs in ({"text": "a [b"}, {"text": "a]"}, {"bottom": "[a [b]]"}):
        with pytest.raises(InvalidRequest, match=r"\[\[ or \]\]"):
            Request(content="x", **kwargs)


def test_justify_values():
    assert Request(content="x", top_justify=False, bottom_justify=True).top_justify is False
    with pytest.raises(InvalidRequest):
        Request(content="x", top_justify="yes")
