# Changelog

## 0.3.1 - 2026-11-16
### Fixed
- Icon previews and the icon browser page work behind Apache on Debian and
  Ubuntu: icon images are served at `/icon/...` and the browser page at
  `/browse`, since those Apache servers map `/icons/` to their own directory
  server-wide.

## 0.3.0 - 2026-11-16
### Changed
- Complete rewrite: core library (`wyltkm.core`), command line tool
  (`wyltkm`) and web app (`wyltkm.web`) as separate parts sharing one engine.
- The SVG is built directly; everything is a filled path (QR modules, finder
  patterns, text, icons). reportlab and svglib are no longer used.
- Designs are TOML files with inheritance, colour fallbacks, an optional list
  `order`, and optional schemes: variants of a design that change its
  colours, fonts or default icon.
- Design variants are schemes: the black and white Attraktor design is the
  scheme `bw` of `attraktor` (`-d attraktor -s bw`, with the mono logo), and
  38c3 light and lighter are the schemes `light` and `lighter` of `38c3`.
- The bottom line is rendered from fonts as a justified text block instead of
  pre-rendered graphics; text lines are as far apart as text and code.
- QR codes always use error correction level H.
- Icons are named `source:name` (e.g. `fa:solid/cat`, `carbon:boot`,
  `attraktor:logo`). Clean break: old URL parameters and icon names are gone.
- New web interface: form and live preview side by side, the code on a
  cutting mat with its measures, design previews with scheme chips, dark and
  light theme with a switch. Works without JavaScript as a plain form.
- Packaging with `pyproject.toml` and uv; Python 3.12 or later.
### Added
- Design `40c3` after the 40c3 style guide: Jersey 10, the 40c3 logo as icon,
  thirteen schemes (twelve colour combinations and black and white for
  engraving).
- All icons of Font Awesome Free 7.3.1, IBM Carbon and the 40c3 style guide,
  read from zip files, with search by name, label and keywords, and an icon
  browser in the web app. Own SVG icons can be uploaded (web) or given as a
  file (`--icon-file`).
- Readable side text: optionally, the content of the code is printed along
  the right side, for people without a scanner (`--side-text`).
- Config file and data directories, where installs add fonts, designs and
  icon sources; system fonts can be switched off.
- Command line tool `wyltkm` (`render`, `designs`, `icons`, `fonts`,
  `licences`, `config`, `web`).
- Licence records for designs, icon sources and fonts; each image lists the
  licences of its parts, and embeds them in the file unless switched off.
- Free fonts bundled: Hack, Jersey 10, Pilowlava, Space Grotesk.
- Cache headers (ETag) for rendered images, previews and icons.
- Documentation in `docs/`, including deployment with a WSGI server or with
  Apache and FastCGI.
- Tests, including decoding of rendered codes and golden files.
### Removed
- WTForms and flask-wtf; the "advanced parameters" page.
- reportlab and svglib.

## 0.2.2 - 2024-11-26
### Added
- Design `38c3light` and `38lighter` that uses SpaceGrotesk on top.

## 0.2.1 - 2024-11-25
### Fixed
- Remove empty square in middle if no icon is selected.

## 0.2.0 - 2024-11-25
### Changed
- Massive internal rewrite.
- Icons are now stored in black only and coloured on the fly.
- Easy creation of new designs.
- Easy adding of new icons.
### Added
- New design `38c3` created after design guide.
- Added a lot of new icons from AwesomeFont.
- Added a few icons from carbon (from the 38c3 design guide).

## 0.1.6 - 2022-10-20
### Changed
- Switch question and info icons to use circle.
- Make switch to advanced parameters to keep values.
### Added
- Rocket Icon introduced for "Project".

## 0.1.5 - 2022-10-19
### Added
- Experimental support for Icons inside QR-Code
- Optional white background.
### Changed
- Individual file name for downloaded files.
- Change colour theme to render "MORE" in blue.

## 0.1.4 - 2022-10-17
### Fixed
- Use cairosvg to correctly render the png preview.
### Added
- PNG button to render image directly to PNG image.

## 0.1.3 - 2022-10-16
### Fixed
- Correct path in MANIFEST.in, so css and favicon work on deployment.

## 0.1.2 - 2022-10-16
### Changed
- Redesign form for QR creation.
- Minimal input options on main page, extra page showing all parameters.
### Fixed
- Can now render texts containing spaces.
### Added
- Add help page.
- Add favicon.
### Known Issues
- Must install ziafont from git-repo for space fix.
- Preview PNG is broken.

## 0.1.1 - 2022-10-14
### Changed
- Completely redesign QR generation.
- Create design for Attraktor WYLTKM QR-Codes.
- Render text to path, so no font is needed for printing
- Use fonts for header text.

## 0.1.0 – 2022-09-30
### Added
- First PoC release.
- QR-codes of three kinds with basic flask app for generation.
