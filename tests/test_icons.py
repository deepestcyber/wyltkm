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
