# Text options

Status: active (2026-11-16); all parts done, waiting for review

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
