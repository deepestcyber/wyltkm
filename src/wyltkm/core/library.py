"""The library: designs, icon sources and fonts of one install."""

from __future__ import annotations

import copy
import threading
from collections import OrderedDict
from pathlib import Path

from .designs import BUILTIN_DIR as BUILTIN_DESIGNS
from .designs import Design, DesignRegistry
from .fonts import BUNDLED_DIR, FontResolver
from .icons import BUILTIN_DIR as BUILTIN_ICONS
from .icons import IconRegistry, IconSource
from .svg import Normalised, normalise

DEFAULT_DESIGN = "attraktor"


class Library:
    """Everything a render needs besides the request. Create once per
    process; it caches loaded designs and fonts."""

    def __init__(self, designs: DesignRegistry, icons: IconRegistry, fonts: FontResolver,
                 default_design: str = DEFAULT_DESIGN, upload_max_elements: int = 5000,
                 upload_max_depth: int = 20):
        self.designs = designs
        self.icons = icons
        self.fonts = fonts
        self.default_design = default_design
        self.upload_max_elements = upload_max_elements
        self.upload_max_depth = upload_max_depth
        self.config = None
        """The ``Config`` this library was made from, if any."""
        self._icons: OrderedDict[tuple[str, str | None], Normalised] = OrderedDict()
        self._icons_lock = threading.Lock()

    ICON_CACHE_SIZE = 256

    def icon(self, name: str, colour: str | None) -> tuple[IconSource, Normalised]:
        """Source and normalised icon ``source:name``, recoloured with
        ``colour`` if the source says so. Cached; the caller gets its own
        copy."""
        src, icon = self.icons.lookup(name)
        colour = colour if src.recolours(icon) else None
        key = (name, colour)
        with self._icons_lock:
            n = self._icons.get(key)
            if n is not None:
                self._icons.move_to_end(key)
        if n is None:
            n = normalise(src.load(icon), recolour=colour, id_prefix="icon-",
                          where=f"icon {name}")
            with self._icons_lock:
                self._icons[key] = n
                while len(self._icons) > self.ICON_CACHE_SIZE:
                    self._icons.popitem(last=False)
        return src, Normalised(copy.deepcopy(n.group), n.viewbox, list(n.warnings))

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

    @classmethod
    def from_config(cls, config=None) -> Library:
        """Library for a configuration; reads the configuration from config
        file and environment when none is given (see docs/configuration.md)."""
        from .config import load
        config = config if config is not None else load()
        lib = cls.builtin(system_fonts=config.system_fonts, default_design=config.default_design,
                          data_dirs=config.data_dirs)
        lib.upload_max_elements = config.web.max_upload_elements
        lib.upload_max_depth = config.web.max_upload_depth
        lib.config = config
        return lib

    def pickable_fonts(self) -> dict:
        """Fonts users may pick for the side text (see ``FontResolver.pickable``)."""
        designs = []
        for name in self.designs.names():
            try:
                designs.append(self.designs.get(name))
            except Exception:  # broken designs are reported elsewhere
                continue
        return self.fonts.pickable(designs)

    def design(self, name: str | None = None) -> Design:
        return self.designs.get(name or self.default_design)
