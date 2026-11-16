# Designs

Status: planned

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
| 1 | Colour schemes in CLI and web | open |
| 2 | Read the 40c3 style guide, define main version and schemes | open |
| 3 | 40c3 design | open |
| 4 | Design previews | open |
| 5 | Docs: adding a design | open |

## 1. Colour schemes in CLI and web

Status: open

The format and loader come with 0001 (part 8). Here:

- `wyltkm designs` and `wyltkm designs show` list schemes with name, title
  and colours, and mark the default scheme.
- `/api/designs` as in [web.md](../web.md), with schemes; built here.
- Web parameter `scheme` and a simple scheme selection in the current
  templates; the polished picker is 0006.

## 2. Read the 40c3 style guide, define main version and schemes

Status: open

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

## 3. 40c3 design

Status: open

- `designs/40c3/design.toml` with named schemes (the main version as
  `default_scheme`), text blocks in
  the 40c3 fonts (Jersey 10, Hack), licence record (CC0).
- Golden-file tests for the main version and each scheme; decode test per
  scheme.

## 4. Design previews

Status: open

- Preview per design and scheme: a sample image rendered on request from
  fixed sample content, cached per process.
- Route `/designs/<name>/preview.svg?scheme=`, preview URLs in
  `/api/designs` ([web.md](../web.md)).
- CLI: `wyltkm designs show <name> --preview -o file.svg` writes the sample.

## 5. Docs: adding a design

Status: open

- Step-by-step in [designs.md](../designs.md), checked by adding one design
  following it.
