# Readable side text

Status: completed (2026-11-16)

Accessibility: on request, the image shows the content of the QR code as
readable text along its right side, so people without a QR scanner can get
the information too. Opt-in per image by the user; the design gives the
default font, colour and sizing, and the user may pick another font.

Background: [rendering.md](../rendering.md) "Readable side text",
[designs.md](../designs.md) `[side]`, [configuration.md](../configuration.md)
"Fonts users can pick". Needs text rendering from 0001 and the font lookup
from 0002.

Status values: `open`, `in progress`, `done`.

| # | Part | Status |
| --- | --- | --- |
| 1 | Design format: `[side]` and `colours.side` | done |
| 2 | Request: `side`, `side_font` | done |
| 3 | Fonts users can pick | done |
| 4 | Layout: rotation, sizing, gap | done |
| 5 | Wrapping into columns | done |
| 6 | CLI and web parameters | done |
| 7 | Tests | done |

## 1. Design format: `[side]` and `colours.side`

Status: done (2026-11-16)

- The loader knows the keys from 0001 (part 8), so designs with `[side]` load
  already. Here they take effect.
- Built-in designs: Hack as default side font (the key's default), side
  colour as their top text colour (the colour's fallback).

Done:

- New keys `side.gap` (default 2) and `side.max_size` (default 3 modules of
  cap height): without a maximum, a short content like `x` filled the whole
  height with one huge letter.

## 2. Request: `side`, `side_font`

Status: done (2026-11-16)

- `side: bool` (default off), `side_font: str | None` (file name).
- The side font must be one of the pickable fonts (part 3); otherwise
  `InvalidRequest`.
- The side font's licence record goes into the render result.

Done:

- `Request.side`, `Request.side_font` (file name syntax checked); whether the
  font is pickable is checked when rendering (`InvalidRequest`, web 400).

## 3. Fonts users can pick

Status: done (2026-11-16)

- List of fonts from `fonts/` of the data directories, the side default font
  of every design, and, if `system_fonts`, the system font directories; by
  file name, without duplicates (first found wins, as in lookup).
- Display name per font for the web selection: the file name without
  extension is enough for now.
- `wyltkm fonts` lists them; `/api/fonts` is built here.

Done:

- `FontResolver.pickable()` / `Library.pickable_fonts()`. With system fonts
  on, this lists every system font (2403 on the development machine); the
  current web form shows them all in one selection. Hosted installs switch
  system fonts off; 0006 should make the selection searchable.

## 4. Layout: rotation, sizing, gap

Status: done (2026-11-16)

- Main column laid out as before; side column to its right with a gap of 2
  modules, inside the border.
- Text rotated by 90° (direction from the design), glyphs as paths, one line
  filling the main column's height.
- The whole layout in module units, scaled to the requested width at the end
  ([rendering.md](../rendering.md)). Check that the existing layout code from
  0001 already works this way, or move it there in this part.

Done:

- The layout was already in module units. The side block is laid out as a
  normal left-aligned text block (`text.block_at`) whose lines are the
  columns, then rotated with a group transform (`rotate(-90)` for `up`,
  `rotate(90)` for `down`).

## 5. Wrapping into columns

Status: done (2026-11-16)

- Below `min_size`, wrap into columns at the break characters listed in
  [rendering.md](../rendering.md); hard breaks only when a piece is still too
  long. Choose the number of columns as small as possible, then the breaks
  that balance the column lengths.
- More than `max_columns` needed: use `max_columns` at a smaller size, with a
  warning.
- Content line breaks are kept as breaks.

Done:

- `core/side.py`: greedy packing on glyph advances (fast), binary search for
  the shortest column length that keeps the number of columns, then the
  exact ink width sets the size.

## 6. CLI and web parameters

Status: done (2026-11-16)

- CLI `--side-text/--no-side-text`, `--side-font`.
- Web parameters `side`, `side_font` on `/` and `/render.*`; simple checkbox
  and font selection in the current templates. The polished UI is part of
  0006.

Done:

- CLI `--side-text/--no-side-text`, `--side-font`; `wyltkm fonts` lists the
  pickable fonts. Web `side`, `side_font`, `/api/fonts`, checkbox and font
  selection in the form.

## 7. Tests

Status: done (2026-11-16)

- Short URL (one column), long URL (several columns), content with line
  breaks, content longer than `max_columns` allow (warning).
- Golden files for both directions.
- The QR code still decodes with side text on (the side text is outside the
  code, but check the gap).

Done:

- `tests/test_side.py`, golden files `side-up-attraktor` and
  `side-long-40c3`, scan tests with side text, CLI and web tests.

