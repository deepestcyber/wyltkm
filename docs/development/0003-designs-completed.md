# Designs

Status: completed (2026-11-16)

Colour schemes in the design format, and the 40c3 design: a main version
and the other colour combinations the style guide allows as schemes.

Background: [designs.md](../designs.md), the style guide in
`40c3-styleguide-full-latest.zip` (`Styleguide.pdf`, palette, fonts, assets),
[style guide page](https://events.ccc.de/congress/2026/infos/styleguide/).
Design and assets are CC0; Jersey 10 and Hack have their own licences,
included in the zip.

Status values: `open`, `in progress`, `done`.

| # | Part | Status |
| --- | --- | --- |
| 1 | Colour schemes in CLI and web | done |
| 2 | Read the 40c3 style guide, define main version and schemes | done |
| 3 | 40c3 design | done |
| 4 | Design previews | done |
| 5 | Docs: adding a design | done |

## 1. Colour schemes in CLI and web

Status: done (2026-11-16)

The format and loader come with 0001 (part 8). Here:

- `wyltkm designs` and `wyltkm designs show` list schemes with name, title
  and colours, and mark the default scheme.
- `/api/designs` as in [web.md](../web.md), with schemes; built here.
- Web parameter `scheme` and a simple scheme selection in the current
  templates; the polished picker is 0006.

Done:

- `wyltkm designs` lists schemes; `wyltkm designs show` lists each scheme
  with its colours and the contrast of modules and finder patterns against
  the background, marked LOW below 3 (`designs.contrast`, WCAG ratio).
- `/api/designs` with schemes, default scheme, licence and preview URLs.
- The scheme selection in the current template appears after a design with
  schemes is chosen and the form is sent again (no JavaScript yet).

## 2. Read the 40c3 style guide, define main version and schemes

Status: done (2026-11-16)

- Palette: 14 colours (`#75B54B`, `#13AEA3`, `#999FCD`, `#B78FBF`, `#EB5D9D`,
  `#EB6F83`, `#F28931`, `#FAB93E`, `#7EAE83`, `#3B5831`, `#B69D93`, `#584744`,
  `#DFEED5`, `#031202`). Fonts: Hack, Jersey 10.
- The main version is the key one: define it from the style guide (colours,
  fonts, bottom line, default icon).
- The style guide allows a lot of variation: derive the other colour
  combinations it allows as schemes. Check contrast of each scheme, so the
  code still scans (dark modules on light background or the reverse, with
  enough difference).
- Check whether the style guide sets rules for QR codes or logos.

Done:

- Style guide V1.4 (18 pages): key colours 0, A, B; "Tricolore" is A, B and
  one colour of your choice; headings in Jersey 10, body in Hack; pixel and
  terminal look. No rules for QR codes. The guide asks to keep WCAG contrast
  in mind.
- Main version `green`; dark schemes for the palette colours 1 to 8 and 10;
  light schemes on A with 9 and 11 ([designs.md](../designs.md), "Built-in
  designs").
- Contrast of all schemes 6.0 to 15.9; all scan.

## 3. 40c3 design

Status: done (2026-11-16)

- `designs/40c3/design.toml` with named schemes (the main version as
  `default_scheme`), text blocks in
  the 40c3 fonts (Jersey 10, Hack), licence record (CC0).
- Golden-file tests for the main version and each scheme; decode test per
  scheme.

Done:

- Square modules and finder patterns. Default icon none for now: the 40c3
  logos come as icons with 0004; then the default icon can be one of them.
- Golden files and decode tests for all twelve schemes.

## 4. Design previews

Status: done (2026-11-16)

- Preview per design and scheme: a sample image rendered on request from
  fixed sample content, cached per process.
- Route `/designs/<name>/preview.svg?scheme=`, preview URLs in
  `/api/designs` ([web.md](../web.md)).
- CLI: `wyltkm designs show <name> --preview -o file.svg` writes the sample.

Done:

- `preview_request()` in the core gives the sample request (example URL,
  design title as text, border). Web caches previews per process
  (`lru_cache`, 256 entries). CLI: `--preview [SCHEME]`.

## 5. Docs: adding a design

Status: done (2026-11-16)

- Step-by-step in [designs.md](../designs.md), checked by adding one design
  following it.

Done:

- Followed by adding a design `hacker` (extends `40c3`, other default scheme)
  in a data directory: `designs show`, `--preview` and `render` work.

Also changed in this unit:

- Line spacing of text blocks is measured from the ink, like the gap to the
  QR code: `line_spacing` (font sizes) is replaced by `gap` and `line_gap`
  (modules) in `[top]` and `[bottom]`; `line_gap` defaults to `gap`, so
  lines are as far apart as text and code. Before, the lines of the bottom
  line were further apart than text and code.

