# Text options

Status: completed (2026-11-16)

Highlighting in the top text, and an own bottom line or none.

Background: [designs.md](../designs.md) "Text blocks",
[rendering.md](../rendering.md), [cli.md](../cli.md), [web.md](../web.md).

Status values: `open`, `in progress`, `done`.

| # | Part | Status |
| --- | --- | --- |
| 1 | `[...]` in the top text | done |
| 2 | Own bottom line or none | done |
| 3 | CLI and web | done |
| 4 | Justified or centred, per text | done |
| 5 | Design `fednet` | done |

## 1. `[...]` in the top text

Status: done (2026-11-16)

- The top text is parsed like the design's bottom lines; highlighted runs use
  `colours.highlight`. Unbalanced brackets are an `InvalidRequest` with the
  hint to write `[[` or `]]` (web 400, CLI exit 1).
- Note: where a design's top colour equals its highlight colour (the dark
  40c3 schemes), highlighting in the top text shows no difference.

## 2. Own bottom line or none

Status: done (2026-11-16)

- `Request.bottom`: `None` the design's bottom line, `""` none (no gap
  either), otherwise own lines with `[...]`, in the design's bottom style
  (fonts of the scheme, justified). Also for designs whose bottom is a
  graphic.

## 3. CLI and web

Status: done (2026-11-16)

- CLI `-b/--bottom` (repeatable), `--no-bottom`.
- Web `bottom_mode` (design, text, none) and `bottom`; in the form a switch
  "Bottom line: Design / Own text / None" with a text field for own text.

## 4. Justified or centred, per text

Status: done (2026-11-16)

- Both texts justified by default: the design default of `top.align` is now
  `justify`. `Request.top_justify` and `Request.bottom_justify` (`None`: the
  design's setting) switch each text; CLI `--top-justify/--top-center`,
  `--bottom-justify/--bottom-center`; web `top_justify`, `bottom_justify` and
  a switch under each text.

## 5. Design `fednet`

Status: done (2026-11-16)

- Homage to the "Would you like to know more?" banner of Starship Troopers,
  after a screenshot on the wiki page of the project. The banner's lettering
  has a "Y" shaped like a U with a long right stem; Phuture ODC (T-26,
  Identikal), which 0.2.0 already used, has the same shapes, Eurostile and
  Michroma do not. Phuture is commercial: not bundled, generic fallback with a
  warning where it is missing. File `PhutureODC-Black.ttf`, also
  `PhutureODCBlack.ttf` as 0.2.0 named it.
- Colours sampled from the screenshot: off-white text, cyan `#67b1d0` for
  MORE, orange emblem. A first scheme on the banner's grey bar (`#857371`)
  was dropped: cyan has too little contrast on it for finder patterns, and
  orange hardly shows. Schemes `night` (default; dark, cyan finder patterns,
  orange emblem), `night-subtle` (emblem in muted blue-grey `#7d8996`),
  `light`, `light-subtle` (emblem in `#8b939c`), `bw`.
- Icon: the Federation emblem, given as an SVG (one filled path, no
  background), as icon source `fednet` with `emblem`, recoloured in the
  design's icon colour (orange; black in `bw`). Licence marked unclear.
