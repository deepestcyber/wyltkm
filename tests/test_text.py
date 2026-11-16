import pytest
import ziafont

from wyltkm.core import DataError
from wyltkm.core.fonts import BUNDLED_DIR
from wyltkm.core.text import Run, block, parse_markers


def test_markers():
    assert parse_markers("TO KNOW [MORE]?") == [Run("TO KNOW "), Run("MORE", True), Run("?")]
    assert parse_markers("a [[b]] c") == [Run("a [b] c")]
    for bad in ("[a", "a]", "[a [b]]x]"):
        with pytest.raises(DataError):
            parse_markers(bad)


def _ink_extents(d: str):
    import re
    nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", d)]
    xs = nums[0::2]
    return min(xs), max(xs)


@pytest.mark.parametrize("align", ["center", "justify"])
def test_block_fills_width(align):
    font = ziafont.Font(str(BUNDLED_DIR / "Hack-Regular.ttf"))
    b = block(font, [[Run("WOULD YOU LIKE")], [Run("TO KNOW "), Run("MORE", True), Run("?")]],
              25, align)
    assert b.height > 0 and b.normal and b.highlight
    lo, hi = _ink_extents(b.normal + b.highlight)
    assert lo == pytest.approx(0, abs=0.05) and hi == pytest.approx(25, abs=0.05)


def test_empty_block():
    font = ziafont.Font()
    assert block(font, [[Run("   ")]], 10) is None
