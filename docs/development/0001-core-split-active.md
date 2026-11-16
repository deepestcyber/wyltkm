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
| 4 | Bundled fonts and basic font lookup | open |
| 5 | Text blocks as paths | open |
| 6 | SVG normalising for icons and assets | open |
| 7 | Layout and assembly, PNG | open |
| 8 | Designs as TOML, built-ins ported | open |
| 9 | Existing icons as `dir` sources | open |
| 10 | CLI: `wyltkm render` | open |
| 11 | Web: port to the core API | open |
| 12 | Licence records and reporting | open |
| 13 | Clean-up, changelog, README | open |

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
- `.gitignore` no longer excludes `*.ttf` and `*.otf` (done 2026-11-16), so
  bundled fonts can be committed.

## 2. Core API

Status: open

- `Request`: frozen dataclass. Fields left `None` mean "default" (from
  config or design). Creating it checks what needs no library: content not
  empty and fits a QR code at level H, width 50 to 10000, name syntax, not
  both icon name and uploaded icon ([outline.md](../outline.md)).
- `render_*` checks what needs the library: design, scheme, icon and font
  exist.
- `Library`: designs, icon sources, fonts; built from built-ins in this unit,
  from config in unit 0002.
- `render_svg(library, request) -> Result` with `svg: str` and
  `warnings: list[str]`; `render_png` likewise with `png: bytes`.
- Errors as own exception types, so CLI and web can map them to exit codes
  and HTTP statuses: `UnknownDesign` and `UnknownIcon` (web 404),
  `InvalidRequest` for everything else, including an unknown scheme or side
  font (web 400).

## 3. QR as paths

Status: open

- Matrix from `qrcode.QRCode(...).get_matrix()`, border 0, error correction
  always H.
- Path builders for the shapes in [rendering.md](../rendering.md): data
  modules merged into one path per colour; finder ring with even-odd fill;
  finder centre.
- The empty centre for the icon: the formula of 0.2.2 as written in
  [rendering.md](../rendering.md); test for several QR versions that the code
  still decodes.
- Test: decode generated codes (e.g. with `zbar`/`pyzbar` or `zxing-cpp` as a
  test dependency) for several contents, with and without the empty centre.

## 4. Bundled fonts and basic font lookup

Status: open

Needed here already, because every ported design draws its bottom line as
text.

- Bundle in `core/data/fonts/`, each with its licence file and a
  `<fontfile>.licence.toml` ([licences.md](../licences.md)):
  - `Hack-Regular.ttf` and `Hack-License.txt` from the 40c3 style guide zip
    (`fonts/`).
  - `jersey-10-latin-400-normal.ttf` and `jersey-10_License.txt` from the
    40c3 zip. The `latin` subset covers Latin-1 (umlauts included); the
    `latin-ext` file only adds further characters and is left out.
  - `Pilowlava-Regular.otf` from the upstream release (Velvetyne, OFL), plus
    `Pilowlava-Atome.otf`, moved here from `wyltkm/static/` (nothing in the
    web app uses it).
  - `SpaceGrotesk-Regular.otf` from the upstream release (OFL).
- Font lookup by file name: design directory (and its parents), the bundled
  fonts, then the system font directories. Data directories and the
  `system_fonts` switch come in 0002.
- Fallback to ziafont's built-in font with a warning.
- Agency FB stays out of the repository. Without it installed, `attraktor`
  renders with the fallback font and a warning, like any design with a
  missing font.

## 5. Text blocks as paths

Status: open

- ziafont glyphs as plain `path` elements (check that `svg2 = False` gives no
  `<use>`; otherwise flatten). Keep or fix the workaround for the empty
  `<path d="Z " />`.
- Own line layout from glyph advances (and kerning where ziafont has it), so
  spacing can be controlled: one font size for all lines, set by the widest
  line; `center` and `justify` alignment; `[...]` highlight markers in design
  text ([designs.md](../designs.md), "Text blocks").
- Used for the top text and the bottom line alike.
- Fonts from the lookup in part 4.

## 6. SVG normalising

Status: open

- Safe parsing; everything but shapes, groups, clip paths and gradients is
  removed ([icons.md](../icons.md), "Normalising").
- Primitives to paths: `rect` (with `rx`/`ry`), `circle`, `ellipse`, `line`,
  `polyline`, `polygon`.
- Inline `style` with fill/stroke resolved into attributes; classes from
  `<style>` blocks resolved for the simple cases Carbon and the style guide
  use.
- Recolouring; invisible shapes (`fill="none"` without stroke) stay
  invisible.
- Detection of strokes, clip paths and gradients for the "not
  laser-friendly" warning.

## 7. Layout and assembly, PNG

Status: open

- Layout as in [rendering.md](../rendering.md); same proportions as 0.2.2, so
  outputs look the same.
- Deterministic output (number format, element order).
- PNG via cairosvg.
- Golden-file tests for a few requests per design, with system fonts off,
  so results do not depend on the machine. `attraktor` goldens therefore use
  the fallback font; its look with Agency FB is checked by hand (part 8).

## 8. Designs as TOML

Status: open

- Loader with validation, defaults and colour fallbacks (key table in
  [designs.md](../designs.md)), `extends` and colour schemes with
  `default_scheme`. No built-in design uses schemes yet; tests use small test
  designs.
- Port `attraktor`, `attraktor-bw`, `38c3`, `38c3-light`, `38c3-lighter`.
  The bottom line becomes a text block in every design (fonts: Agency FB,
  Pilowlava, Space Grotesk); all `wyltkm-*.svg` bottom graphics are deleted.
  Compare the output side by side with 0.2.2 renders, on a machine with
  Agency FB installed.
- The default design comes from the config (`attraktor` until 0002 adds the
  config file); nothing in the code treats `attraktor` specially.
- Built-in registry only; data directories come in 0002.

## 9. Existing icons as `dir` sources

Status: open

- `dir` source type, source TOML files with `rename` tables, the icon name
  syntax `source:name` and the file-name rule ([icons.md](../icons.md)).
- Current icons: `attraktor:logo`, `attraktor:logo-mono` (via `rename`), the
  Carbon subset as `carbon:*`. The Font Awesome subset in `res/awesome` is
  replaced in 0004; until then its files move into `solid/` and `brands/`
  subdirectories without the `-solid`/`-brands-solid` suffix, so names are
  already `fa:solid/cat`, `fa:brands/github`.

## 10. CLI: `wyltkm render`

Status: open

- click, with help texts for every command and option.
- `wyltkm render` with the options in [cli.md](../cli.md), except those that
  come later: `--icon-file` (0004), `--side-text`/`--side-font` (0005).
  `--scheme` works already (part 8).
- `wyltkm designs`, `wyltkm designs show`, `wyltkm icons` and
  `wyltkm licences` in simple form. `wyltkm config` and `wyltkm fonts` come
  in 0002, `wyltkm icons list/search/show` in 0004.
- Exit codes and warnings on stderr.

## 11. Web: port to the core API

Status: open

- `create_app()` factory, routes `/`, `/render.svg`, `/render.png`, `/help`
  with the new parameter names. Parameters are read into `Request` directly;
  WTForms and flask-wtf are removed. Current templates kept for now; the real
  redesign is 0006.
- `wyltkm web` starts the development server (only with the web extra
  installed; otherwise a clear message).

## 12. Licence records and reporting

Status: open

- Licence records as in [licences.md](../licences.md) for the built-in
  designs, icon sources and bundled fonts.
- The render result collects the records of the parts used.
- SVG `<metadata>`, PNG `tEXt` chunk; on by default, off with
  `Request.licence_metadata = False`.
- CLI: attribution note on stderr, `--licences`, `--no-licence-metadata`,
  `wyltkm licences`.
- Web: licence box under the preview, `licence_metadata` parameter and
  checkbox, `/api/licences`, and a `/licences` page, simple form;
  polished in 0006.
- Attraktor design and logo get a record with licence "unclear" (holder
  Attraktor e.V.) until clarified; 38c3 is CC0.
- Add `LICENCE.md` next to the 40c3 zip with the CC0 statement and source URL.

## 13. Clean-up, changelog, README

Status: open

- Remove `generate.py`, `style.py`, `icon.py`, the dead code and unused
  resources.
- README: short description, install, links to docs.
- Changelog entry; version 0.3.0.

## Open questions

- None at the moment.
