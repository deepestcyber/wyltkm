# Readable side text

Status: planned

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
| 1 | Design format: `[side]` and `colours.side` | open |
| 2 | Request: `side`, `side_font` | open |
| 3 | Fonts users can pick | open |
| 4 | Layout: rotation, sizing, gap | open |
| 5 | Wrapping into columns | open |
| 6 | CLI and web parameters | open |
| 7 | Tests | open |

## 1. Design format: `[side]` and `colours.side`

Status: open

- The loader knows the keys from 0001 (part 8), so designs with `[side]` load
  already. Here they take effect.
- Built-in designs: Hack as default side font (the key's default), side
  colour as their top text colour (the colour's fallback).

## 2. Request: `side`, `side_font`

Status: open

- `side: bool` (default off), `side_font: str | None` (file name).
- The side font must be one of the pickable fonts (part 3); otherwise
  `InvalidRequest`.
- The side font's licence record goes into the render result.

## 3. Fonts users can pick

Status: open

- List of fonts from `fonts/` of the data directories, the side default font
  of every design, and, if `system_fonts`, the system font directories; by
  file name, without duplicates (first found wins, as in lookup).
- Display name per font for the web selection: the file name without
  extension is enough for now.
- `wyltkm fonts` lists them; `/api/fonts` is built here.

## 4. Layout: rotation, sizing, gap

Status: open

- Main column laid out as before; side column to its right with a gap of 2
  modules, inside the border.
- Text rotated by 90° (direction from the design), glyphs as paths, one line
  filling the main column's height.
- The whole layout in module units, scaled to the requested width at the end
  ([rendering.md](../rendering.md)). Check that the existing layout code from
  0001 already works this way, or move it there in this part.

## 5. Wrapping into columns

Status: open

- Below `min_size`, wrap into columns at the break characters listed in
  [rendering.md](../rendering.md); hard breaks only when a piece is still too
  long. Choose the number of columns as small as possible, then the breaks
  that balance the column lengths.
- More than `max_columns` needed: use `max_columns` at a smaller size, with a
  warning.
- Content line breaks are kept as breaks.

## 6. CLI and web parameters

Status: open

- CLI `--side-text/--no-side-text`, `--side-font`.
- Web parameters `side`, `side_font` on `/` and `/render.*`; simple checkbox
  and font selection in the current templates. The polished UI is part of
  0006.

## 7. Tests

Status: open

- Short URL (one column), long URL (several columns), content with line
  breaks, content longer than `max_columns` allow (warning).
- Golden files for both directions.
- The QR code still decodes with side text on (the side text is outside the
  code, but check the gap).
