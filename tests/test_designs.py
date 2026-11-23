import textwrap

import pytest

from wyltkm.core import DataError, InvalidRequest, UnknownDesign
from wyltkm.core.designs import DesignRegistry


def _write(root, name, body):
    d = root / name
    d.mkdir(parents=True)
    (d / "design.toml").write_text(f'name = "{name}"\n' + textwrap.dedent(body))


def test_builtins_load(library):
    for d in library.designs.all():
        assert d.title
        assert set(d.colours()) >= {"background", "modules", "highlight", "side"}


def test_40c3_contrast(library):
    """All 40c3 schemes keep a clear contrast between code and background."""
    from wyltkm.core.designs import contrast
    d = library.design("40c3")
    assert d.default_scheme == "green" and len(d.schemes) == 13
    for s in d.schemes.values():
        c = s.colours
        for key in ("modules", "finder_ring", "finder_centre"):
            assert contrast(c[key], c["background"]) >= 4.5, (s.name, key)


def test_contrast():
    from wyltkm.core.designs import contrast
    assert contrast("#000000", "#ffffff") == pytest.approx(21)
    assert contrast("#123456", "#123456") == pytest.approx(1)


def test_gaps(tmp_path):
    _write(tmp_path, "g", '''
        title = "G"
        [colours]
        background = "#ffffff"
        modules = "#000000"
        [top]
        gap = 3
        [bottom]
        type = "text"
        lines = ["X"]
        line_gap = 1
        ''')
    d = DesignRegistry([tmp_path]).get("g")
    assert (d.top.gap, d.top.line_gap) == (3, 3)
    assert (d.bottom.style.gap, d.bottom.style.line_gap) == (2, 1)


def test_colour_fallbacks(tmp_path):
    _write(tmp_path, "a", '''
        title = "A"
        [colours]
        background = "#FFFFFF"
        modules = "#000001"
        top = "#000002"
        ''')
    c = DesignRegistry([tmp_path]).get("a").colours()
    assert c["background"] == "#ffffff"
    assert c["finder_ring"] == c["finder_centre"] == c["icon"] == "#000001"
    assert c["bottom"] == c["highlight"] == c["side"] == "#000002"


def test_schemes_and_merge_order(tmp_path):
    _write(tmp_path, "parent", '''
        title = "P"
        default_scheme = "one"
        [colours]
        background = "#000000"
        modules = "#000001"
        top = "#000002"
        [schemes.one]
        title = "One"
        modules = "#000011"
        [schemes.two]
        title = "Two"
        top = "#000022"
        ''')
    _write(tmp_path, "child", '''
        title = "C"
        extends = "parent"
        [colours]
        modules = "#000100"
        top = "#000200"
        [schemes.two]
        modules = "#002200"
        ''')
    reg = DesignRegistry([tmp_path])
    child = reg.get("child")
    assert list(child.schemes) == ["one", "two"]
    one, two = child.colours("one"), child.colours("two")
    # parent colours < child colours < parent scheme < child scheme
    assert one["modules"] == "#000011" and one["top"] == "#000200"
    assert two["modules"] == "#002200" and two["top"] == "#000022"
    assert child.colours() == one
    with pytest.raises(InvalidRequest):
        child.colours("three")
    assert child.licence.name == "unknown"
    assert [p.name for p in child.dirs] == ["child", "parent"]


def test_scheme_on_design_without_schemes(tmp_path):
    _write(tmp_path, "plain", '''
        title = "Plain"
        [colours]
        background = "#ffffff"
        modules = "#000000"
        ''')
    with pytest.raises(InvalidRequest):
        DesignRegistry([tmp_path]).get("plain").colours("main")


def test_scheme_fonts(library, tmp_path):
    d = library.design("38c3")
    assert d.top_style("pilowlava").fonts == d.top_style().fonts == ("Pilowlava-Regular.otf",)
    assert d.top_style("light").fonts == ("SpaceGrotesk-Regular.otf",)
    assert d.bottom_style("light").fonts == ("Pilowlava-Regular.otf",)
    assert d.bottom_style("lighter").fonts == ("SpaceGrotesk-Regular.otf",)
    assert d.bottom_style("lighter").align == "justify"  # only the fonts change
    assert d.side_fonts("lighter") == ("Hack-Regular.ttf",)
    _write(tmp_path, "x", '''
        title = "X"
        default_scheme = "a"
        [colours]
        background = "#ffffff"
        modules = "#000000"
        [schemes.a]
        title = "A"
        fonts = { middle = ["x.ttf"] }
        ''')
    with pytest.raises(DataError, match="schemes.a.fonts"):
        DesignRegistry([tmp_path]).get("x")


def test_scheme_default_icon(library, tmp_path):
    d = library.design("attraktor")
    assert d.default_icon() == d.default_icon("colour") == "attraktor:logo"
    assert d.default_icon("bw") == "attraktor:logo-mono"
    assert d.colours("bw")["icon"] == "#000000"
    _write(tmp_path, "x", '''
        title = "X"
        default_scheme = "a"
        [colours]
        background = "#ffffff"
        modules = "#000000"
        [schemes.a]
        title = "A"
        default_icon = "nonsense"
        ''')
    with pytest.raises(DataError, match="default_icon"):
        DesignRegistry([tmp_path]).get("x")


@pytest.mark.parametrize("body, msg", [
    ('title = "X"\ncolour = 1\n', "unknown keys"),
    ('title = "X"\n[qr]\nshape = "x"\n', "unknown keys"),
    ('title = "X"\n[colours]\nbackground = "#fff"\nmodules = "#000000"\n', "#rrggbb"),
    ('title = "X"\n[colours]\nbackground = "#ffffff"\n', "modules is required"),
    ('title = "X"\nextends = "x"\n[colours]\nbackground = "#ffffff"\nmodules = "#000000"\n',
     "cycle"),
    ('title = "X"\n[colours]\nbackground = "#ffffff"\nmodules = "#000000"\n'
     '[bottom]\ntype = "text"\nlines = ["[a"]\n', "without"),
    ('title = "X"\n[colours]\nbackground = "#ffffff"\nmodules = "#000000"\n'
     '[schemes.a]\ntitle = "A"\n', "default_scheme"),
])
def test_broken_designs(tmp_path, body, msg):
    _write(tmp_path, "x", body)
    with pytest.raises(DataError, match=msg):
        DesignRegistry([tmp_path]).get("x")


def test_unknown_and_override(tmp_path, library):
    with pytest.raises(UnknownDesign):
        library.design("nope")
    _write(tmp_path, "attraktor", '''
        title = "Mine"
        [colours]
        background = "#ffffff"
        modules = "#000000"
        ''')
    from wyltkm.core.designs import BUILTIN_DIR
    assert DesignRegistry([tmp_path, BUILTIN_DIR]).get("attraktor").title == "Mine"


def test_fednet(library):
    d = library.design("fednet")
    assert d.default_scheme == "night"
    assert set(d.schemes) == {"night", "night-subtle", "light", "light-subtle", "bw"}
    assert d.colours("bw")["finder_ring"] == d.colours("bw")["finder_centre"] == "#000000"
    assert d.top_style().fonts[0] == "PhutureODC-Black.ttf"
    assert d.default_icon() == "fa:solid/jet-fighter"
    src, icon = library.icons.lookup("fednet:emblem")
    assert src.recolours(icon)
    from wyltkm.core.designs import contrast
    for s in d.schemes.values():
        for key in ("modules", "finder_ring", "finder_centre"):
            assert contrast(s.colours[key], s.colours["background"]) >= 4, (s.name, key)


def test_order(library, tmp_path):
    assert [d.name for d in library.ordered_designs()] == ["attraktor", "40c3", "38c3", "fednet"]
    _write(tmp_path, "zz", 'title = "Z"\norder = 1\n[colours]\nbackground = "#ffffff"\n'
                           'modules = "#000000"\n')
    _write(tmp_path, "aa", 'title = "A"\n[colours]\nbackground = "#ffffff"\nmodules = "#000000"\n')
    from wyltkm.core import Library
    from wyltkm.core.designs import BUILTIN_DIR
    lib = Library(DesignRegistry([tmp_path, BUILTIN_DIR]), library.icons, library.fonts)
    assert [d.name for d in lib.ordered_designs()] == ["attraktor", "zz", "40c3", "38c3", "fednet",
                                                       "aa"]
