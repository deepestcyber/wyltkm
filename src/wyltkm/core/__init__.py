"""WYLTKM core: turns a request into an SVG or PNG image.

Public API::

    from wyltkm.core import Library, Request, render_svg, render_png

    library = Library.builtin()
    result = render_svg(library, Request(content="https://example.org", text="Hello"))
    result.svg, result.warnings, result.licences

Everything else in this package is internal.
"""

from .config import Config, WebConfig
from .errors import DataError, InvalidRequest, UnknownDesign, UnknownIcon, WyltkmError
from .library import Library
from .licences import Licence
from .render import Result, licence_text, render_png, render_svg
from .request import Request

__all__ = [
    "Config", "DataError", "InvalidRequest", "WebConfig", "Library", "Licence", "Request", "Result", "UnknownDesign",
    "UnknownIcon", "WyltkmError", "licence_text", "render_png", "render_svg",
]
