"""Font lookup by file name (see docs/configuration.md, "Fonts")."""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import ziafont

from . import licences
from .licences import Licence

ziafont.config.svg2 = False
ziafont.config.precision = 3

BUNDLED_DIR = Path(str(resources.files("wyltkm.core") / "data" / "fonts"))
FONT_SUFFIXES = (".ttf", ".otf")

FALLBACK_LICENCE = Licence(
    part="Font DejaVuSans.ttf (fallback)",
    name="Bitstream-Vera",
    url="https://dejavu-fonts.github.io/License.html",
    holder="Bitstream, Inc.; DejaVu changes public domain",
)


def system_font_dirs() -> list[Path]:
    home = Path.home()
    data_home = Path(os.environ.get("XDG_DATA_HOME") or home / ".local" / "share")
    return [data_home / "fonts", home / ".fonts", Path("/usr/local/share/fonts"),
            Path("/usr/share/fonts")]


@dataclass(frozen=True)
class FontRef:
    """A loaded font with where it came from."""

    name: str
    """File name, or "" for the fallback font."""
    path: Path | None
    font: ziafont.Font
    licence: Licence


class FontResolver:
    """Finds fonts by file name.

    Order: the given design directories, then ``font_dirs`` (data
    directories' ``fonts/`` and the bundled fonts), then system font
    directories (recursively) if ``system_fonts``.
    """

    def __init__(self, font_dirs: list[Path] | None = None, system_fonts: bool = True):
        self.font_dirs = list(font_dirs) if font_dirs is not None else [BUNDLED_DIR]
        self.system_fonts = system_fonts
        self._system_index: dict[str, Path] | None = None
        self._loaded: dict[Path | None, FontRef] = {}

    def _system(self) -> dict[str, Path]:
        if self._system_index is None:
            index: dict[str, Path] = {}
            for base in system_font_dirs():
                if not base.is_dir():
                    continue
                for root, dirs, files in os.walk(base):
                    dirs.sort()
                    for file in sorted(files):
                        if file.lower().endswith(FONT_SUFFIXES):
                            index.setdefault(file, Path(root) / file)
            self._system_index = index
        return self._system_index

    def find(self, name: str, design_dirs: list[Path] = ()) -> Path | None:
        """Path of the font file ``name``, or None."""
        if not name or "/" in name or "\\" in name or name.startswith("."):
            return None
        for base in [*design_dirs, *self.font_dirs]:
            candidate = base / name
            if candidate.is_file():
                return candidate
        if self.system_fonts:
            return self._system().get(name)
        return None

    def available(self) -> dict[str, Path]:
        """Font files in the font directories (not system fonts), by file
        name; the first one found wins, as in lookup."""
        out: dict[str, Path] = {}
        for base in self.font_dirs:
            if base.is_dir():
                for f in sorted(base.iterdir()):
                    if f.is_file() and f.name.lower().endswith(FONT_SUFFIXES):
                        out.setdefault(f.name, f)
        return out

    def pickable(self, designs=()) -> dict[str, Path]:
        """Fonts users may pick for the side text: the font directories, the
        side default font of each given design, and system fonts if they are
        searched. By file name, first found wins, sorted by name."""
        out = dict(self.available())
        for d in designs:
            for scheme in [None, *d.schemes]:
                for name in d.side_fonts(scheme):
                    path = self.find(name, list(d.dirs))
                    if path is not None:
                        out.setdefault(name, path)
                        break
        if self.system_fonts:
            for name, path in self._system().items():
                out.setdefault(name, path)
        return dict(sorted(out.items(), key=lambda kv: kv[0].lower()))

    def load(self, path: Path | None) -> FontRef:
        if path not in self._loaded:
            if path is None:
                ref = FontRef("", None, ziafont.Font(), FALLBACK_LICENCE)
            else:
                ref = FontRef(path.name, path, ziafont.Font(str(path)), licences.for_font(path))
            self._loaded[path] = ref
        return self._loaded[path]

    def resolve(self, names: list[str] | tuple[str, ...], design_dirs: list[Path] = (),
                warnings: list[str] | None = None) -> FontRef:
        """First font of ``names`` that is found; else the fallback font.

        An empty list means the fallback font on purpose, without warning.
        """
        for name in names:
            path = self.find(name, design_dirs)
            if path is not None:
                return self.load(path)
        if names and warnings is not None:
            warnings.append(f"font not found: {', '.join(names)}; using fallback font")
        return self.load(None)
