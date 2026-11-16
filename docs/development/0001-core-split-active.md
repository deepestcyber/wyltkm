# Core split

Status: active (2026-11-16)

Split the project into core library, CLI and web app, on a new renderer that
builds the SVG itself and emits paths only. At the end, everything 0.2.2 can
do works on the new structure (with the new parameter names), and the
reportlab/svglib chain is gone. Configuration, fonts, new designs, new icon
sources and the web redesign follow in later units.

Background: [outline.md](../outline.md), [rendering.md](../rendering.md),
[designs.md](../designs.md).

Status values: `open`, `in progress`, `done`.

| # | Part | Status |
| --- | --- | --- |
| 1 | Packaging: pyproject, uv, src layout, pytest | open |
| 2 | Core API: `Library`, `Request`, `render_svg`, `render_png` | open |
| 3 | QR as paths | open |
| 4 | Text blocks as paths | open |
| 5 | SVG normalising for icons and assets | open |
| 6 | Layout and assembly, PNG | open |
| 7 | Designs as TOML, built-ins ported | open |
| 8 | Existing icons as `dir` sources | open |
| 9 | CLI: `wyltkm render` | open |
| 10 | Web: port to the core API | open |
| 11 | Licence records and reporting | open |
| 12 | Clean-up, changelog, README | open |

## 1. Packaging: pyproject, uv, src layout, pytest

Status: open

- `pyproject.toml` with hatchling, Python ≥ 3.12, `uv.lock`.
- Move the package to `src/wyltkm/`, subpackages `core`, `cli`, `web`.
- Base dependencies (core and CLI): `qrcode`, `ziafont`, `cairosvg`, a safe
  XML parser (`defusedxml` or `lxml` with safe settings), `click`. Extra
  `web`: `flask`,
  `python-slugify`. No WTForms or flask-wtf.
- Console script `wyltkm = wyltkm.cli:main`.
- `setup.py`, `requirements.txt` and `MANIFEST.in` go away; package data via
  hatchling.
- pytest set up, one smoke test.
- Commit the two zips in `res/` and move them to their new place in
  `core/data/`.

## 2. Core API

Status: open

- `Request`: frozen dataclass with validation (content not empty and fits a QR
  code, width range, icon name syntax).
- `Library`: designs, icon sources, fonts; built from built-ins in this unit,
  from config in unit 0002.
- `render_svg(library, request) -> Result` with `svg: str` and
  `warnings: list[str]`; `render_png` likewise with `png: bytes`.
- Errors as own exception types (`UnknownDesign`, `UnknownIcon`,
  `InvalidRequest`), so CLI and web can map them to exit codes and HTTP
  statuses.

## 3. QR as paths

Status: open

- Matrix from `qrcode.QRCode(...).get_matrix()`, border 0.
- Path builders for the shapes in [rendering.md](../rendering.md): data
  modules merged into one path per colour; finder ring with even-odd fill;
  finder centre.
- The empty centre for the icon: keep today's formula, document it, test it
  for several QR versions that the code still decodes.
- Test: decode generated codes (e.g. with `zbar`/`pyzbar` or `zxing-cpp` as a
  test dependency) for several contents, with and without the empty centre.

## 4. Text blocks as paths

Status: open

- ziafont glyphs as plain `path` elements (check that `svg2 = False` gives no
  `<use>`; otherwise flatten). Keep or fix the workaround for the empty
  `<path d="Z " />`.
- Own line layout from glyph advances (and kerning where ziafont has it), so
  spacing can be controlled: one font size for all lines, set by the widest
  line; `center` and `justify` alignment; `[...]` highlight markers in design
  text ([designs.md](../designs.md), "Text blocks").
- Used for the top text and the bottom line alike.
- Font given as a path for now; lookup comes in 0002.

## 5. SVG normalising

Status: open

- Safe parsing, removal of everything not shape or group.
- Primitives to paths: `rect` (with `rx`/`ry`), `circle`, `ellipse`, `line`,
  `polyline`, `polygon`.
- Inline `style` with fill/stroke resolved into attributes; classes from
  `<style>` blocks resolved for the simple cases Carbon and the style guide
  use.
- Recolouring.
- Detection of strokes, clip paths and gradients for the "not
  laser-friendly" warning.

## 6. Layout and assembly, PNG

Status: open

- Layout as in [rendering.md](../rendering.md); same proportions as 0.2.2, so
  outputs look the same.
- Deterministic output (number format, element order).
- PNG via cairosvg.
- Golden-file tests for a few requests per design.

## 7. Designs as TOML

Status: open

- Loader with validation and `extends`.
- Port `attraktor`, `attraktor-bw`, `38c3`, `38c3-light`, `38c3-lighter`.
  The bottom line becomes a text block in every design (fonts: Agency FB,
  Pilowlava, Space Grotesk); all `wyltkm-*.svg` bottom graphics are deleted.
  Compare the output side by side with 0.2.2 renders.
- Built-in registry only; data directories come in 0002.

## 8. Existing icons as `dir` sources

Status: open

- `dir` source type and the icon name syntax `source:name`.
- Current icons: `attraktor:logo`, `attraktor:logo-mono`, the Carbon subset as
  `carbon:*`. The Font Awesome subset in `res/awesome` is replaced in 0004;
  until then it stays as an `fa` dir source with names like `fa:solid/cat`.

## 9. CLI: `wyltkm render`

Status: open

- click, with help texts for every command and option. `wyltkm render`
  with the options in [cli.md](../cli.md) (scheme options come with 0003),
  plus `wyltkm designs`, `wyltkm icons` and `wyltkm licences` in simple form.
- Exit codes and warnings on stderr.

## 10. Web: port to the core API

Status: open

- `create_app()` factory, routes `/`, `/render.svg`, `/render.png`, `/help`
  with the new parameter names. Parameters are read into `Request` directly;
  WTForms and flask-wtf are removed. Current templates kept for now; the real
  redesign is 0006.

## 11. Licence records and reporting

Status: open

- Licence records as in [licences.md](../licences.md) for the built-in
  designs, icon sources and bundled fonts.
- The render result collects the records of the parts used.
- SVG `<metadata>`, PNG `tEXt` chunk; on by default, off with
  `Request.licence_metadata = False`.
- CLI: attribution note on stderr, `--licences`, `--no-licence-metadata`,
  `wyltkm licences`.
- Web: licence box under the preview, `licence_metadata` parameter and
  checkbox, and a `/licences` page, simple form;
  polished in 0006.
- Attraktor design and logo get a record with licence "unclear" (holder
  Attraktor e.V.) until clarified; 38c3 is CC0.
- Add `LICENCE.md` next to the 40c3 zip with the CC0 statement and source URL.

## 12. Clean-up, changelog, README

Status: open

- Remove `generate.py`, `style.py`, `icon.py`, the dead code and unused
  resources.
- README: short description, install, links to docs.
- Changelog entry; version 0.3.0.

## Open questions

- None at the moment.
