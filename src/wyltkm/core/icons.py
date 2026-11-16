"""Icon sources and the icon registry (see docs/icons.md)."""

from __future__ import annotations

import logging
import re
import tomllib
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

from . import licences
from .errors import DataError, UnknownIcon
from .licences import Licence
from .request import valid_icon_name, valid_name

log = logging.getLogger(__name__)

BUILTIN_DIR = Path(str(resources.files("wyltkm.core") / "data" / "icons"))
SOURCE_KEYS = {"name", "title", "type", "path", "prefix", "recolour", "recolour_except",
               "metadata", "rename", "licence"}


def name_from_file(rel: str) -> str:
    """Icon name from a file path below the source's prefix (without .svg):
    lower-cased, ``_`` and spaces become ``-``."""
    return re.sub(r"[_ ]", "-", rel.lower())


@dataclass
class IconSource:
    """A set of icons from a directory (zip sources come with plan 0004)."""

    name: str
    title: str
    recolour: bool
    recolour_except: tuple[str, ...]
    licence: Licence
    files: dict[str, Path] = field(default_factory=dict)
    """Icon name to file."""

    def names(self) -> list[str]:
        return sorted(self.files)

    def recolours(self, icon: str) -> bool:
        """Whether this icon is recoloured: the source setting, inverted for
        names (or folders ending in ``/``) listed in ``recolour_except``."""
        hit = any(icon == e or (e.endswith("/") and icon.startswith(e))
                  for e in self.recolour_except)
        return self.recolour != hit

    def load(self, icon: str) -> bytes:
        path = self.files.get(icon)
        if path is None:
            raise UnknownIcon(f"unknown icon: {self.name}:{icon}")
        return path.read_bytes()


def load_source(toml_path: Path) -> IconSource:
    where = str(toml_path)
    try:
        raw = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise DataError(f"{where}: {e}") from e
    extra = set(raw) - SOURCE_KEYS
    if extra:
        raise DataError(f"{where}: unknown keys: {', '.join(sorted(extra))}")
    name = raw.get("name")
    if not isinstance(name, str) or not valid_name(name) or name != toml_path.stem:
        raise DataError(f"{where}: name must be the file name without .toml")
    if raw.get("type") != "dir":
        raise DataError(f"{where}: type must be 'dir'")
    rel = raw.get("path")
    if not isinstance(rel, str) or not rel:
        raise DataError(f"{where}: path is required")
    base = (toml_path.parent / rel).resolve()
    if not base.is_dir():
        raise DataError(f"{where}: directory {base} not found")
    rename = raw.get("rename") or {}
    if not isinstance(rename, dict) or not all(isinstance(v, str) for v in rename.values()):
        raise DataError(f"{where}: rename must map file names to icon names")
    exceptions = raw.get("recolour_except") or []
    if not isinstance(exceptions, list) or not all(isinstance(e, str) for e in exceptions):
        raise DataError(f"{where}: recolour_except must be a list of icon names")
    recolour = raw.get("recolour", True)
    if not isinstance(recolour, bool):
        raise DataError(f"{where}: recolour must be true or false")
    part = f"Icons {raw.get('title') or name}"
    licence = (licences.from_table(part, raw["licence"], where) if "licence" in raw
               else licences.unknown(part))
    src = IconSource(name=name, title=raw.get("title") or name, recolour=recolour,
                     recolour_except=tuple(exceptions), licence=licence)
    for file in sorted(base.rglob("*.svg")):
        stem = file.relative_to(base).as_posix()[:-4]
        icon = rename.get(stem, name_from_file(stem))
        if not valid_icon_name(f"{name}:{icon}"):
            log.warning("%s: skipping %s, no valid icon name", where, file)
            continue
        src.files.setdefault(icon, file)
    return src


class IconRegistry:
    """Icon sources by name, from icon root directories (first wins)."""

    def __init__(self, roots: list[Path] | None = None):
        self.roots = list(roots) if roots is not None else [BUILTIN_DIR]
        self._sources: dict[str, IconSource] = {}
        for root in self.roots:
            if not root.is_dir():
                continue
            for toml_path in sorted(root.glob("*.toml")):
                if toml_path.stem in self._sources:
                    log.info("icon source %s in %s overrides another", toml_path.stem, root)
                    continue
                self._sources[toml_path.stem] = load_source(toml_path)

    def sources(self) -> list[IconSource]:
        return [self._sources[k] for k in sorted(self._sources)]

    def source(self, name: str) -> IconSource:
        src = self._sources.get(name)
        if src is None:
            raise UnknownIcon(f"unknown icon source: {name}")
        return src

    def lookup(self, full: str) -> tuple[IconSource, str]:
        """Source and icon name for ``source:name``; raises ``UnknownIcon``."""
        if not valid_icon_name(full):
            raise UnknownIcon(f"unknown icon: {full}")
        source, icon = full.split(":", 1)
        src = self.source(source)
        if icon not in src.files:
            raise UnknownIcon(f"unknown icon: {full}")
        return src, icon
