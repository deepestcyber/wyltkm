import importlib.resources
import io
from typing import TextIO

from svglib.svglib import svg2rlg

from wyltkm import res
from wyltkm.res import carbon, awesome

def colour_awesome(svg: TextIO, colour: str|None) -> TextIO:
    if colour:
        return io.StringIO(svg.read().replace("<path d=", "<path style=\"fill:" + colour + "\" d="))
    else:
        return svg


def colour_carbon(svg: TextIO, colour: str|None) -> TextIO:
    if colour:
        return io.StringIO(svg.read().replace("<style>", "<style>* { fill: " + colour + "; }"))
    else:
        return svg


def colour_replace(svg: TextIO, colour: str|None) -> TextIO:
    if colour:
        return io.StringIO(svg.read().replace("#ffffff", colour))
    else:
        return svg


def load_icon(icon: str, colour: str|None) -> TextIO|None:
    f: TextIO|None = None
    if icon == "attraktor":
        f = importlib.resources.open_text(res, f"attraktor.svg")
    elif icon == "attraktor-mono":
        f = importlib.resources.open_text(res, f"attraktor-mono.svg")
        f = colour_replace(f, colour)
    elif icon.startswith("carbon/"):
        try:
            f = importlib.resources.open_text(carbon, f"{icon[7:]}.svg")
        except FileNotFoundError:
            return None
        f = colour_carbon(f, colour)
    else:
        try:
            f = importlib.resources.open_text(awesome, f"{icon}.svg")
        except FileNotFoundError:
            return None
        f = colour_awesome(f, colour)
    return f
