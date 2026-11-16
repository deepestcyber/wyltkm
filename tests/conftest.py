import pytest

from wyltkm.core import Library, config


@pytest.fixture(scope="session")
def library():
    """Built-in library without system fonts, so results are the same on
    every machine."""
    return Library.builtin(system_fonts=False)


@pytest.fixture(autouse=True)
def isolated_env(tmp_path_factory, monkeypatch):
    """No config file, data directory or system font of the machine leaks
    into the tests."""
    base = tmp_path_factory.mktemp("env")
    for key in ("WYLTKM_CONFIG", "WYLTKM_DATA_DIRS"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(base / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(base / "data"))
    monkeypatch.setenv("XDG_DATA_DIRS", str(base / "system-data"))
    monkeypatch.setattr(config, "SYSTEM_CONFIG", base / "etc" / "config.toml")
    import wyltkm.cli
    monkeypatch.setattr(wyltkm.cli, "_LIBRARY", None)
    return base
