# Changelog

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
