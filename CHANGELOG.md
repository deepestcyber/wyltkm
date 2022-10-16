# Changelog

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
