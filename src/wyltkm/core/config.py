"""Configuration: config file, data directories, environment
(see docs/configuration.md)."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from .errors import DataError
from .library import DEFAULT_DESIGN
from .request import MAX_WIDTH, MIN_WIDTH, valid_name

SYSTEM_CONFIG = Path("/etc/wyltkm/config.toml")
TOP_KEYS = {"default_design", "data_dirs", "system_fonts", "web"}
WEB_KEYS = {"max_width", "max_upload_bytes", "max_upload_elements", "max_upload_depth"}


@dataclass(frozen=True)
class WebConfig:
    max_width: int = 4000
    max_upload_bytes: int = 256 * 1024
    max_upload_elements: int = 5000
    max_upload_depth: int = 20


@dataclass(frozen=True)
class DataDir:
    path: Path
    origin: str
    """Where it came from: "config", "WYLTKM_DATA_DIRS", "XDG_DATA_HOME", "XDG_DATA_DIRS"."""

    @property
    def exists(self) -> bool:
        return self.path.is_dir()


@dataclass(frozen=True)
class Config:
    path: Path | None = None
    """The config file in use, or None for defaults."""
    default_design: str = DEFAULT_DESIGN
    system_fonts: bool = True
    candidates: tuple[DataDir, ...] = ()
    """All data directories in search order, also those that do not exist."""
    web: WebConfig = field(default_factory=WebConfig)

    @property
    def data_dirs(self) -> list[Path]:
        """Existing data directories in search order (without the package's)."""
        seen, out = set(), []
        for d in self.candidates:
            key = d.path.resolve()
            if d.exists and key not in seen:
                seen.add(key)
                out.append(d.path)
        return out


def _env(env, key: str) -> str:
    return (env.get(key) or "").strip()


def config_path(env=None, system_config: Path | None = None) -> Path | None:
    """The config file to use, in the documented search order."""
    env = os.environ if env is None else env
    explicit = _env(env, "WYLTKM_CONFIG")
    if explicit:
        path = Path(explicit).expanduser()
        if not path.is_file():
            raise DataError(f"WYLTKM_CONFIG: {path} is not a file")
        return path
    home = _env(env, "XDG_CONFIG_HOME") or str(Path.home() / ".config")
    for path in (Path(home) / "wyltkm" / "config.toml", system_config or SYSTEM_CONFIG):
        if path.is_file():
            return path
    return None


def _int(table: dict, key: str, default: int, lo: int, hi: int, where: str) -> int:
    v = table.get(key, default)
    if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
        raise DataError(f"{where}: {key} must be a whole number from {lo} to {hi}")
    return v


def _parse(raw: dict, path: Path) -> tuple[dict, list[DataDir], WebConfig]:
    where = str(path)
    extra = set(raw) - TOP_KEYS
    if extra:
        raise DataError(f"{where}: unknown keys: {', '.join(sorted(extra))}")
    values = {}
    if "default_design" in raw:
        if not isinstance(raw["default_design"], str) or not valid_name(raw["default_design"]):
            raise DataError(f"{where}: default_design must be a design name")
        values["default_design"] = raw["default_design"]
    if "system_fonts" in raw:
        if not isinstance(raw["system_fonts"], bool):
            raise DataError(f"{where}: system_fonts must be true or false")
        values["system_fonts"] = raw["system_fonts"]
    dirs = raw.get("data_dirs", [])
    if not isinstance(dirs, list) or not all(isinstance(d, str) and d for d in dirs):
        raise DataError(f"{where}: data_dirs must be a list of directories")
    # relative paths are relative to the config file
    data = [DataDir(path.parent / Path(d).expanduser(), "config") for d in dirs]
    w = raw.get("web", {})
    if not isinstance(w, dict):
        raise DataError(f"{where}: web must be a table")
    extra = set(w) - WEB_KEYS
    if extra:
        raise DataError(f"{where}: unknown keys in [web]: {', '.join(sorted(extra))}")
    web = WebConfig(
        max_width=_int(w, "max_width", 4000, MIN_WIDTH, MAX_WIDTH, f"{where} [web]"),
        max_upload_bytes=_int(w, "max_upload_bytes", 256 * 1024, 1, 1024 * 1024, f"{where} [web]"),
        max_upload_elements=_int(w, "max_upload_elements", 5000, 1, 100000, f"{where} [web]"),
        max_upload_depth=_int(w, "max_upload_depth", 20, 1, 100, f"{where} [web]"),
    )
    return values, data, web


def load(env=None, system_config: Path | None = None) -> Config:
    """Read the configuration from config file and environment."""
    env = os.environ if env is None else env
    path = config_path(env, system_config)
    values: dict = {}
    data: list[DataDir] = []
    web = WebConfig()
    if path is not None:
        try:
            raw = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as e:
            raise DataError(f"{path}: {e}") from e
        values, data, web = _parse(raw, path)
    for d in _env(env, "WYLTKM_DATA_DIRS").split(":"):
        if d:
            data.append(DataDir(Path(d).expanduser(), "WYLTKM_DATA_DIRS"))
    data_home = _env(env, "XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    data.append(DataDir(Path(data_home) / "wyltkm", "XDG_DATA_HOME"))
    for d in (_env(env, "XDG_DATA_DIRS") or "/usr/local/share:/usr/share").split(":"):
        if d:
            data.append(DataDir(Path(d) / "wyltkm", "XDG_DATA_DIRS"))
    return Config(path=path, candidates=tuple(data), web=web, **values)
