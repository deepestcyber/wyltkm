"""Exceptions of the core.

CLI and web map them to exit codes and HTTP statuses: ``UnknownDesign`` and
``UnknownIcon`` mean "not found" (web 404), everything else is an invalid
request (web 400). ``DataError`` is a broken design, icon source or config
file, a problem of the install rather than of the request.
"""


class WyltkmError(Exception):
    """Base class of all errors of the core."""


class InvalidRequest(WyltkmError):
    """The request is not valid (bad value, unknown scheme or font, ...)."""


class UnknownDesign(WyltkmError):
    """No design with this name."""


class UnknownIcon(WyltkmError):
    """No icon with this name, or no source with this name."""


class DataError(WyltkmError):
    """A design, icon source or other data file is broken."""
