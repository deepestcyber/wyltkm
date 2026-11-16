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
| 1 | Colour schemes in the design format | open |
| 2 | Read the 40c3 style guide, define main version and schemes | open |
| 3 | 40c3 design | open |
| 4 | Design previews | open |
| 5 | Docs: adding a design | open |

## 1. Colour schemes in the design format

Status: open

- `[schemes.<name>]` tables as in [designs.md](../designs.md), inherited by
  child designs.
- `Request.scheme`, CLI `--scheme`, web parameter `scheme`; unknown scheme is
  an error.
- `wyltkm designs` and `/api/designs` list schemes with title and colours.

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

- `designs/40c3/design.toml` with main colours and schemes, text blocks in
  the 40c3 fonts (Jersey 10, Hack), licence record (CC0).
- Golden-file tests for the main version and each scheme; decode test per
  scheme.

## 4. Design previews

Status: open

- A small preview per design and scheme (rendered sample), used by
  `wyltkm designs` and the web pickers.

## 5. Docs: adding a design

Status: open

- Step-by-step in [designs.md](../designs.md), checked by adding one design
  following it.
