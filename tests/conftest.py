import pytest

from wyltkm.core import Library


@pytest.fixture(scope="session")
def library():
    """Built-in library without system fonts, so results are the same on
    every machine."""
    return Library.builtin(system_fonts=False)
