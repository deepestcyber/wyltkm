"""The request: what image to make.

Creating a ``Request`` checks everything that needs no library (syntax,
ranges, content length). Whether design, scheme, icon and fonts exist is
checked when rendering.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import qrcode
import qrcode.exceptions

from .errors import InvalidRequest

DEFAULT_WIDTH = 250
MIN_WIDTH = 50
MAX_WIDTH = 10000
MAX_ICON_BYTES = 1024 * 1024
NO_ICON = "none"

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FONT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._+-]*\.(ttf|otf|TTF|OTF)$")
ICON_RE = re.compile(r"^[a-z0-9][a-z0-9-]*:[a-z0-9-]+(/[a-z0-9-]+)*$")


def valid_name(name: str) -> bool:
    """Syntax of design, scheme and source names."""
    return bool(NAME_RE.match(name)) and len(name) <= 64


def valid_icon_name(name: str) -> bool:
    """Syntax of icon names ``source:name``, with ``/`` for folders."""
    return bool(ICON_RE.match(name)) and len(name) <= 200


def fits_qr(content: str) -> bool:
    """Whether the content fits a QR code at error correction level H."""
    qr = qrcode.QRCode(error_correction=qrcode.ERROR_CORRECT_H, border=0)
    qr.add_data(content)
    try:
        qr.make(fit=True)
    except (qrcode.exceptions.DataOverflowError, ValueError):
        return False
    return True


PREVIEW_CONTENT = "https://example.org/would-you-like-to-know-more"


def preview_request(design: str, scheme: str | None = None, title: str = "Preview",
                    width: int = 200) -> "Request":
    """The fixed sample request used for design previews."""
    return Request(content=PREVIEW_CONTENT, text=title, design=design, scheme=scheme,
                   width=width, border=True)


@dataclass(frozen=True)
class Request:
    """What to render. ``None`` means "default" (from config or design)."""

    content: str
    """Data in the QR code, usually a URL."""
    text: str = ""
    """Top text; ``\\n`` separates lines. Empty: no top text."""
    design: str | None = None
    scheme: str | None = None
    icon: str | None = None
    """Icon name ``source:name``, or ``"none"`` for no icon."""
    icon_svg: bytes | None = None
    """An uploaded icon (SVG file content); not together with ``icon``."""
    width: int = DEFAULT_WIDTH
    """Width of the whole image in px."""
    border: bool | None = None
    background: bool | None = None
    licence_metadata: bool = True
    """Put licence info into the image file."""
    side: bool = False
    """Readable side text with the content."""
    side_font: str | None = None
    """Font file name for the side text; default from the design."""

    def __post_init__(self):
        if not isinstance(self.content, str) or not self.content:
            raise InvalidRequest("content must not be empty")
        if not isinstance(self.text, str):
            raise InvalidRequest("text must be a string")
        if self.design is not None and not valid_name(self.design):
            raise InvalidRequest(f"invalid design name: {self.design!r}")
        if self.scheme is not None and not valid_name(self.scheme):
            raise InvalidRequest(f"invalid scheme name: {self.scheme!r}")
        if self.icon is not None and self.icon != NO_ICON and not valid_icon_name(self.icon):
            raise InvalidRequest(f"invalid icon name: {self.icon!r} (expected source:name or none)")
        if self.icon is not None and self.icon_svg is not None:
            raise InvalidRequest("give either an icon name or an icon file, not both")
        if self.icon_svg is not None:
            if not isinstance(self.icon_svg, bytes) or not self.icon_svg:
                raise InvalidRequest("icon file is empty")
            if len(self.icon_svg) > MAX_ICON_BYTES:
                raise InvalidRequest(f"icon file is larger than {MAX_ICON_BYTES} bytes")
        if isinstance(self.width, bool) or not isinstance(self.width, int):
            raise InvalidRequest("width must be a whole number")
        if not MIN_WIDTH <= self.width <= MAX_WIDTH:
            raise InvalidRequest(f"width must be between {MIN_WIDTH} and {MAX_WIDTH}")
        if self.side_font is not None and (not FONT_RE.match(self.side_font)
                                           or len(self.side_font) > 200):
            raise InvalidRequest(f"invalid font file name: {self.side_font!r}")
        if not fits_qr(self.content):
            raise InvalidRequest("content is too long for a QR code")

    @property
    def lines(self) -> list[str]:
        """Top text lines; trailing empty lines removed."""
        lines = self.text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        while lines and not lines[-1].strip():
            lines.pop()
        while lines and not lines[0].strip():
            lines.pop(0)
        return lines
