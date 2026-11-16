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


def _y_extents(d: str):
    import re
    nums = [float(v) for v in re.findall(r"-?\d+\.?\d*", d)]
    ys = nums[1::2]
    return min(ys), max(ys)


@pytest.mark.parametrize("font_file", ["jersey-10-latin-400-normal.ttf", "Hack-Regular.ttf",
                                       "Pilowlava-Regular.otf"])
def test_line_gap_is_measured_from_the_ink(font_file):
    font = ziafont.Font(str(BUNDLED_DIR / font_file))
    one = block(font, [[Run("WOULD YOU LIKE")], [Run("TO KNOW")]], 25, "center", line_gap=2)
    first = block(font, [[Run("WOULD YOU LIKE")]], 25)
    second = block(font, [[Run("WOULD YOU LIKE")], [Run("TO KNOW")]], 25, "center", line_gap=5)
    # the second line moves down by exactly the difference of the gaps
    assert second.height - one.height == pytest.approx(3, abs=0.01)
    # first line ink ends at its height; the next line starts line_gap below
    lo, _ = _y_extents(one.normal.split("M ")[-1])  # some glyph of line 2
    assert lo >= first.height + 2 - 0.01
