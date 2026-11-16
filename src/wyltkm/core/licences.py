"""Licence records of designs, icon sources and fonts (see docs/licences.md)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from .errors import DataError

_KEYS = {"name", "url", "holder", "attribution", "requires_attribution", "file"}


@dataclass(frozen=True, order=True)
class Licence:
    """Licence of one part of an image."""

    part: str
    """What the record is about, e.g. "Design attraktor" or "Font Hack-Regular.ttf"."""
    name: str
    """SPDX id where one exists, else a short name; "unknown" if there is no record."""
    url: str = ""
    holder: str = ""
    attribution: str = ""
    requires_attribution: bool = False
    file: str = ""
    """Licence text file next to the part, if any."""

    @property
    def needs_note(self) -> bool:
        """Whether the user should be told about it after rendering."""
        return self.requires_attribution or self.name in ("unclear", "unknown")

    def text(self) -> str:
        """One line for humans."""
        parts = [f"{self.part}: {self.name}"]
        if self.holder:
            parts.append(self.holder)
        if self.url:
            parts.append(self.url)
        line = ", ".join(parts)
        if self.requires_attribution and self.attribution:
            line += f'. Attribution: "{self.attribution}"'
        return line


def unknown(part: str) -> Licence:
    return Licence(part=part, name="unknown")


def from_table(part: str, table: dict, where: str) -> Licence:
    """Licence from a TOML table; ``where`` names the file for errors."""
    if not isinstance(table, dict):
        raise DataError(f"{where}: licence must be a table")
    extra = set(table) - _KEYS
    if extra:
        raise DataError(f"{where}: unknown licence keys: {', '.join(sorted(extra))}")
    if not isinstance(table.get("name"), str) or not table["name"]:
        raise DataError(f"{where}: licence needs a name")
    for key in ("url", "holder", "attribution", "file"):
        if not isinstance(table.get(key, ""), str):
            raise DataError(f"{where}: licence {key} must be a string")
    if not isinstance(table.get("requires_attribution", False), bool):
        raise DataError(f"{where}: licence requires_attribution must be true or false")
    return Licence(part=part, **table)


def for_font(font_file: Path) -> Licence:
    """Licence record next to a font file, or "unknown"."""
    part = f"Font {font_file.name}"
    record = font_file.with_name(font_file.name + ".licence.toml")
    if not record.is_file():
        return unknown(part)
    try:
        table = tomllib.loads(record.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise DataError(f"{record}: {e}") from e
    return from_table(part, table, str(record))
