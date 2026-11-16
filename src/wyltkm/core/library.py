"""The library: designs, icon sources and fonts of one install."""

from __future__ import annotations

from pathlib import Path

from .designs import BUILTIN_DIR as BUILTIN_DESIGNS
from .designs import Design, DesignRegistry
from .fonts import BUNDLED_DIR, FontResolver
from .icons import BUILTIN_DIR as BUILTIN_ICONS
from .icons import IconRegistry

DEFAULT_DESIGN = "attraktor"


class Library:
    """Everything a render needs besides the request. Create once per
    process; it caches loaded designs and fonts."""

    def __init__(self, designs: DesignRegistry, icons: IconRegistry, fonts: FontResolver,
                 default_design: str = DEFAULT_DESIGN):
        self.designs = designs
        self.icons = icons
        self.fonts = fonts
        self.default_design = default_design

    @classmethod
    def builtin(cls, system_fonts: bool = True, default_design: str = DEFAULT_DESIGN,
                data_dirs: list[Path] = ()) -> Library:
        """Built-in designs, icons and fonts, plus ``designs/``, ``icons/``
        and ``fonts/`` of the given data directories (searched first)."""
        dirs = [Path(d) for d in data_dirs]
        return cls(
            designs=DesignRegistry([*(d / "designs" for d in dirs), BUILTIN_DESIGNS]),
            icons=IconRegistry([*(d / "icons" for d in dirs), BUILTIN_ICONS]),
            fonts=FontResolver([*(d / "fonts" for d in dirs), BUNDLED_DIR],
                               system_fonts=system_fonts),
            default_design=default_design,
        )

    def design(self, name: str | None = None) -> Design:
        return self.designs.get(name or self.default_design)
