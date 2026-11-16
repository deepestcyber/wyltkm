import textwrap

import pytest

from wyltkm.core import DataError, Library, Request, render_svg
from wyltkm.core import config as cfgmod
from wyltkm.core.config import load


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text))
    return path


def test_defaults(isolated_env):
    c = load()
    assert c.path is None and c.default_design == "attraktor" and c.system_fonts
    assert c.data_dirs == []
    assert [d.origin for d in c.candidates] == ["XDG_DATA_HOME", "XDG_DATA_DIRS"]


def test_search_order(isolated_env, monkeypatch):
    xdg = _write(isolated_env / "config" / "wyltkm" / "config.toml", 'default_design = "a"\n')
    etc = _write(cfgmod.SYSTEM_CONFIG, 'default_design = "b"\n')
    explicit = _write(isolated_env / "x.toml", 'default_design = "c"\n')
    assert load().path == xdg
    xdg.unlink()
    assert load().path == etc
    monkeypatch.setenv("WYLTKM_CONFIG", str(explicit))
    assert load().default_design == "c"
    monkeypatch.setenv("WYLTKM_CONFIG", str(isolated_env / "missing.toml"))
    with pytest.raises(DataError):
        load()


def test_data_dirs_order(isolated_env, monkeypatch):
    for name in ("conf", "env1", "env2", "data/wyltkm", "system-data/wyltkm"):
        (isolated_env / name).mkdir(parents=True)
    path = _write(isolated_env / "c.toml", 'data_dirs = ["conf", "missing"]\n')
    monkeypatch.setenv("WYLTKM_CONFIG", str(path))
    monkeypatch.setenv("WYLTKM_DATA_DIRS", f"{isolated_env / 'env1'}:{isolated_env / 'env2'}")
    c = load()
    assert [p.relative_to(isolated_env).as_posix() for p in c.data_dirs] == [
        "conf", "env1", "env2", "data/wyltkm", "system-data/wyltkm"]
    assert not next(d for d in c.candidates if d.path.name == "missing").exists


@pytest.mark.parametrize("text, msg", [
    ("colour = 1\n", "unknown keys"),
    ("[web]\nmax_hight = 1\n", "unknown keys"),
    ("[web]\nmax_width = 20000\n", "max_width"),
    ("system_fonts = 1\n", "system_fonts"),
    ("default_design = 'Bad Name'\n", "default_design"),
    ("data_dirs = 'x'\n", "data_dirs"),
    ("x = \n", "c.toml"),
])
def test_invalid(isolated_env, monkeypatch, text, msg):
    monkeypatch.setenv("WYLTKM_CONFIG", str(_write(isolated_env / "c.toml", text)))
    with pytest.raises(DataError, match=msg):
        load()


def test_library_from_data_dir(isolated_env, monkeypatch, library):
    """A data directory adds designs, icon sources and fonts, and overrides
    built-in designs; config switches system fonts off and sets limits."""
    data = isolated_env / "srv"
    _write(data / "designs" / "mine" / "design.toml", '''
        name = "mine"
        title = "Mine"
        [colours]
        background = "#ffffff"
        modules = "#000000"
        [top]
        fonts = ["MyFont.ttf"]
        ''')
    (data / "fonts").mkdir()
    import shutil
    from wyltkm.core.fonts import BUNDLED_DIR
    shutil.copy(BUNDLED_DIR / "Hack-Regular.ttf", data / "fonts" / "MyFont.ttf")
    _write(data / "fonts" / "MyFont.ttf.licence.toml", 'name = "OFL-1.1"\n')
    (data / "icons" / "mine").mkdir(parents=True)
    (data / "icons" / "mine" / "dot.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><circle cx=".5" cy=".5" r=".5"/></svg>')
    _write(data / "icons" / "mine.toml", 'name = "mine"\ntype = "dir"\npath = "mine"\n')
    conf = _write(isolated_env / "c.toml", f'''
        default_design = "mine"
        data_dirs = ["{data}"]
        system_fonts = false
        [web]
        max_upload_elements = 3
        ''')
    monkeypatch.setenv("WYLTKM_CONFIG", str(conf))
    lib = Library.from_config()
    assert lib.default_design == "mine" and not lib.fonts.system_fonts
    assert lib.upload_max_elements == 3
    r = render_svg(lib, Request(content="x", text="Hi", icon="mine:dot"))
    parts = {lic.part: lic.name for lic in r.licences}
    assert parts["Font MyFont.ttf"] == "OFL-1.1" and "Icons mine" in parts
    assert not r.warnings
    assert "MyFont.ttf" in lib.fonts.available()
