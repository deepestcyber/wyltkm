"""Icon sources, the icon registry and search (see docs/icons.md)."""

from __future__ import annotations

import json
import logging
import re
import threading
import tomllib
import zipfile
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

from . import licences
from .errors import DataError, UnknownIcon
from .licences import Licence
from .request import valid_icon_name, valid_name

log = logging.getLogger(__name__)

BUILTIN_DIR = Path(str(resources.files("wyltkm.core") / "data" / "icons"))
SOURCE_KEYS = {"name", "title", "type", "path", "prefix", "include", "recolour",
               "recolour_except", "metadata", "rename", "licence"}
METADATA_READERS = {"fontawesome", "carbon"}


def name_from_file(rel: str) -> str:
    """Icon name from a file path below the source's prefix (without .svg):
    lower-cased, ``_`` and spaces become ``-``."""
    return re.sub(r"[_ ]", "-", rel.lower())


@dataclass(frozen=True)
class IconInfo:
    """Search data of one icon."""

    label: str = ""
    terms: tuple[str, ...] = ()


@dataclass
class IconSource:
    """A set of icons from a directory or a zip file."""

    name: str
    title: str
    recolour: bool
    recolour_except: tuple[str, ...]
    licence: Licence
    files: dict[str, str] = field(default_factory=dict)
    """Icon name to file: a path for ``dir`` sources, a member for ``zip``."""
    zip_path: Path | None = None
    metadata: str | None = None
    prefix: str = ""
    _info: dict[str, IconInfo] | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def names(self) -> list[str]:
        return sorted(self.files)

    def recolours(self, icon: str) -> bool:
        """Whether this icon is recoloured: the source setting, inverted for
        names (or folders ending in ``/``) listed in ``recolour_except``."""
        hit = any(icon == e or (e.endswith("/") and icon.startswith(e))
                  for e in self.recolour_except)
        return self.recolour != hit

    def load(self, icon: str) -> bytes:
        """The SVG file of an icon."""
        member = self.files.get(icon)
        if member is None:
            raise UnknownIcon(f"unknown icon: {self.name}:{icon}")
        try:
            if self.zip_path is None:
                return Path(member).read_bytes()
            with zipfile.ZipFile(self.zip_path) as z:
                return z.read(member)
        except (OSError, KeyError, zipfile.BadZipFile) as e:
            raise DataError(f"icon source {self.name}: cannot read {icon}: {e}") from e

    def info(self, icon: str) -> IconInfo:
        """Label and search terms of an icon (empty without metadata)."""
        return self._metadata().get(icon, IconInfo())

    def _metadata(self) -> dict[str, IconInfo]:
        with self._lock:
            if self._info is None:
                self._info = _read_metadata(self) if self.metadata else {}
            return self._info


def _read_metadata(src: IconSource) -> dict[str, IconInfo]:
    """Read labels and search terms; a broken metadata file only disables
    search by label and terms."""
    try:
        with zipfile.ZipFile(src.zip_path) as z:
            members = z.namelist()
            if src.metadata == "fontawesome":
                member = next(m for m in members if m.endswith("metadata/icons.json"))
                data = json.loads(z.read(member))
                out = {}
                for key, meta in data.items():
                    info = IconInfo(meta.get("label", ""),
                                    tuple(meta.get("search", {}).get("terms", [])))
                    for style in meta.get("free", []):
                        out[name_from_file(f"{style}/{key}")] = info
                return out
            if src.metadata == "carbon":
                data = json.loads(z.read("metadata.json"))
                out = {}
                for meta in data["icons"]:
                    rel = ("svg/" + meta["file"])[len(src.prefix):-4]
                    out[name_from_file(rel)] = IconInfo(meta.get("label", ""),
                                                        tuple(meta.get("terms", [])))
                return out
    except (OSError, KeyError, ValueError, StopIteration, zipfile.BadZipFile) as e:
        log.warning("icon source %s: cannot read metadata: %s", src.name, e)
    return {}


def _check_str_list(raw, key, where):
    v = raw.get(key) or []
    if not isinstance(v, list) or not all(isinstance(e, str) for e in v):
        raise DataError(f"{where}: {key} must be a list of strings")
    return v


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
    kind = raw.get("type")
    if kind not in ("dir", "zip"):
        raise DataError(f"{where}: type must be 'dir' or 'zip'")
    rel = raw.get("path")
    if not isinstance(rel, str) or not rel:
        raise DataError(f"{where}: path is required")
    base = (toml_path.parent / rel).resolve()
    prefix = raw.get("prefix", "")
    if not isinstance(prefix, str) or (prefix and not prefix.endswith("/")):
        raise DataError(f"{where}: prefix must be a path ending in /")
    include = _check_str_list(raw, "include", where)
    rename = raw.get("rename") or {}
    if not isinstance(rename, dict) or not all(isinstance(v, str) for v in rename.values()):
        raise DataError(f"{where}: rename must map file names to icon names")
    exceptions = _check_str_list(raw, "recolour_except", where)
    recolour = raw.get("recolour", True)
    if not isinstance(recolour, bool):
        raise DataError(f"{where}: recolour must be true or false")
    metadata = raw.get("metadata")
    if metadata is not None and (metadata not in METADATA_READERS or kind != "zip"):
        raise DataError(f"{where}: metadata must be one of {', '.join(sorted(METADATA_READERS))} "
                        "(zip sources only)")
    title = raw.get("title") or name
    part = f"Icons {title}"
    licence = (licences.from_table(part, raw["licence"], where) if "licence" in raw
               else licences.unknown(part))
    src = IconSource(name=name, title=title, recolour=recolour,
                     recolour_except=tuple(exceptions), licence=licence, metadata=metadata,
                     prefix=prefix)

    if kind == "dir":
        if not base.is_dir():
            raise DataError(f"{where}: directory {base} not found")
        entries = [(f.relative_to(base).as_posix(), str(f)) for f in base.rglob("*.svg")]
    else:
        if not base.is_file():
            raise DataError(f"{where}: zip file {base} not found")
        try:
            with zipfile.ZipFile(base) as z:
                members = z.namelist()
        except (OSError, zipfile.BadZipFile) as e:
            raise DataError(f"{where}: {base}: {e}") from e
        src.zip_path = base
        entries = [(m[len(prefix):], m) for m in members
                   if m.startswith(prefix) and m.lower().endswith(".svg") and "/../" not in m]
    for rel_path, member in sorted(entries):
        if include and not any(rel_path.startswith(i) for i in include):
            continue
        stem = rel_path[:-4]
        icon = rename.get(stem, name_from_file(stem))
        if not valid_icon_name(f"{name}:{icon}"):
            log.info("%s: skipping %s, no valid icon name", where, rel_path)
            continue
        if icon in src.files:
            log.info("%s: skipping %s, name %s already taken", where, rel_path, icon)
            continue
        src.files[icon] = member
    return src


@dataclass(frozen=True)
class Hit:
    name: str
    """Full icon name ``source:name``."""
    label: str
    rank: int


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

    def search(self, query: str, source: str | None = None, limit: int = 50) -> list[Hit]:
        """Icons matching all words of ``query``, best first.

        Rank per word: exact name (last part) 0, name starts with it 1, name
        contains it 2, label contains it 3, a search term starts with it 4.
        An icon's rank is that of its worst word; ties sorted by name.
        """
        words = [w for w in re.split(r"[\s:]+", query.lower().strip()) if w]
        sources = [self.source(source)] if source else self.sources()
        hits: list[Hit] = []
        for src in sources:
            for icon in src.names():
                info = src.info(icon) if words else IconInfo()
                worst = 0
                for w in words:
                    rank = _rank(w, icon, info)
                    if rank is None:
                        break
                    worst = max(worst, rank)
                else:
                    hits.append(Hit(f"{src.name}:{icon}", info.label, worst))
        hits.sort(key=lambda h: (h.rank, h.name))
        return hits[:limit] if limit else hits


def _rank(word: str, icon: str, info: IconInfo) -> int | None:
    last = icon.rsplit("/", 1)[-1]
    if last == word:
        return 0
    if last.startswith(word):
        return 1
    if word in icon:
        return 2
    if word in info.label.lower():
        return 3
    if any(t.lower().startswith(word) for t in info.terms):
        return 4
    return None
