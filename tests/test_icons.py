import pytest

from wyltkm.core import DataError, UnknownIcon
from wyltkm.core.icons import IconRegistry, name_from_file


def test_name_rule():
    assert name_from_file("Icons_Deco/Icon_Cat") == "icons-deco/icon-cat"
    assert name_from_file("A b") == "a-b"


def test_builtin_sources(library):
    names = {s.name for s in library.icons.sources()}
    assert {"attraktor", "carbon", "fa"} <= names
    src, icon = library.icons.lookup("attraktor:logo")
    assert not src.recolours("logo") and src.recolours("logo-mono")
    assert library.icons.lookup("fa:brands/github")[1] == "brands/github"
    for bad in ("fa:solid/nope", "nope:x", "fa:../x"):
        with pytest.raises(UnknownIcon):
            library.icons.lookup(bad)


def test_dir_source_rename_and_skip(tmp_path):
    (tmp_path / "s" / "Sub").mkdir(parents=True)
    svg = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><path d="M0 0H1V1Z"/></svg>'
    (tmp_path / "s" / "Sub" / "My_Icon.svg").write_bytes(svg)
    (tmp_path / "s" / "odd!name.svg").write_bytes(svg)
    (tmp_path / "s" / "x.svg").write_bytes(svg)
    (tmp_path / "s.toml").write_text('name = "s"\ntype = "dir"\npath = "s"\n'
                                     '[rename]\n"x" = "nicer"\n')
    src = IconRegistry([tmp_path]).source("s")
    assert src.names() == ["nicer", "sub/my-icon"]
    assert src.licence.name == "unknown"


def test_broken_source(tmp_path):
    (tmp_path / "s.toml").write_text('name = "other"\ntype = "dir"\npath = "."\n')
    with pytest.raises(DataError):
        IconRegistry([tmp_path])


SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><path d="M0 0H1V1Z"/></svg>'


def _zip_source(tmp_path, toml_extra=""):
    import zipfile
    with zipfile.ZipFile(tmp_path / "set.zip", "w") as z:
        z.writestr("pkg/svgs/A/One_Icon.svg", SVG)
        z.writestr("pkg/svgs/A/two.svg", SVG)
        z.writestr("pkg/svgs/B/three.svg", SVG)
        z.writestr("pkg/svgs/readme.txt", b"x")
        z.writestr("other/four.svg", SVG)
    (tmp_path / "z.toml").write_text('name = "z"\ntype = "zip"\npath = "set.zip"\n'
                                     'prefix = "pkg/svgs/"\n' + toml_extra)
    return IconRegistry([tmp_path]).source("z")


def test_zip_source(tmp_path):
    src = _zip_source(tmp_path)
    assert src.names() == ["a/one-icon", "a/two", "b/three"]
    assert src.load("a/two") == SVG


def test_zip_source_include_and_recolour_except(tmp_path):
    src = _zip_source(tmp_path, 'include = ["B/"]\nrecolour = false\nrecolour_except = ["b/"]\n')
    assert src.names() == ["b/three"]
    assert src.recolours("b/three")


def test_builtin_zip_sources(library):
    fa = library.icons.source("fa")
    assert len(fa.files) > 2000 and {"solid/cat", "regular/heart", "brands/github"} <= set(fa.files)
    assert fa.info("solid/cat").label == "Cat" and "kitten" in fa.info("solid/cat").terms
    carbon = library.icons.source("carbon")
    assert len(carbon.files) > 2700 and carbon.info("boot").label == "Boot"
    forty = library.icons.source("40c3")
    assert {"logos/40c3-logo-a", "citizens/blahaj", "icons-deco/icon-cat"} <= set(forty.files)
    assert forty.recolours("logos/40c3-logo-a") and not forty.recolours("citizens/blahaj")
    assert forty.licence.name == "CC0-1.0"


def test_search_ranking(library):
    names = [h.name for h in library.icons.search("cat", limit=10)]
    assert names[0] == "fa:solid/cat"
    hits = library.icons.search("kitten")  # only a search term of fa:solid/cat
    assert "fa:solid/cat" in [h.name for h in hits]
    assert [h.name for h in library.icons.search("arrow up", source="carbon", limit=3)] == [
        "carbon:arrow--up", "carbon:arrow--up-left", "carbon:arrow--up-right"]
    assert library.icons.search("zzzzqqq") == []
    with pytest.raises(UnknownIcon):
        library.icons.search("x", source="nope")


def test_icon_cache_returns_copies(library):
    _, a = library.icon("fa:solid/cat", "#ff0000")
    a.group.clear()
    _, b = library.icon("fa:solid/cat", "#ff0000")
    assert len(b.group) > 0
    _, c = library.icon("fa:solid/cat", "#00ff00")
    assert next(c.group.iter("path")).get("fill") == "#00ff00"


def test_render_icon(library):
    from wyltkm.core import render_icon
    svg = render_icon(library, "40c3:citizens/blahaj")
    assert svg.startswith("<?xml") and "clipPath" in svg
    assert 'fill="#123456"' in render_icon(library, "carbon:boot", "#123456")


def test_every_builtin_icon_normalises(library):
    """All icons of all built-in sources can be placed (a few thousand)."""
    from wyltkm.core.svg import normalise
    bad = []
    for src in library.icons.sources():
        for icon in src.names():
            try:
                normalise(src.load(icon), where=f"{src.name}:{icon}")
            except DataError as e:
                bad.append(str(e))
    assert not bad, bad[:5]


def test_switch_draws_first_child():
    from wyltkm.core.svg import normalise
    n = normalise(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><switch>'
                  b'<foreignObject/><g><path d="M0 0H1V1Z"/></g><g><path d="M0 0H1Z"/></g>'
                  b'</switch></svg>')
    assert len(list(n.group.iter("path"))) == 1


def test_folders_and_find(library):
    fa = library.icons.source("fa")
    assert set(fa.folders()) == {"brands", "regular", "solid"}
    assert sum(fa.folders().values()) == len(fa.files)
    assert library.icons.source("attraktor").folders() == {"": 2}
    everything = library.icons.find()
    assert len(everything) == sum(len(s.files) for s in library.icons.sources())
    brands = library.icons.find("", "fa", "brands")
    assert len(brands) == fa.folders()["brands"] and all("brands/" in h.name for h in brands)
    assert all(h.label for h in brands)  # aliases without metadata are left out
    assert "fa:solid/arrow-alt-circle-up" not in [h.name for h in library.icons.find("arrow")]
