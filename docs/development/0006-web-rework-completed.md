# Web rework

Status: completed (2026-11-16)

A web interface that is easy to use and looks good: live preview, design
picker, icon search and upload, clean download. Server-rendered, small vanilla
JavaScript, no build step.

Background: [web.md](../web.md).

Status values: `open`, `in progress`, `done`.

| # | Part | Status |
| --- | --- | --- |
| 1 | Visual direction and layout | done |
| 2 | Form and live preview | done |
| 3 | Design picker | done |
| 4 | Icon picker with search and upload | done |
| 5 | Caching | done |
| 6 | Help page, licences page and footer | done |
| 7 | Deployment docs and example config | done |

## 1. Visual direction and layout

Status: done (2026-11-16)

- Agree on a look (sketch first): two columns on wide screens, preview on top
  on phones, works without JavaScript.
- Dark and light theme.

Done:

- Direction agreed from a static sketch: practical, workshop-exact, a little
  playful; quiet graphite chrome with one accent (Attraktor blue from the
  favicon); the colour lives in the preview, where the code lies on a
  cutting mat with crop marks and its measures (the signature detail).
  Space Grotesk and Hack, served from the package (`/ui-fonts/`), so the
  page loads nothing external.
- Dark and light theme from the system, plus a switch in the header
  (system, dark, light) remembered in `localStorage`; the choice is applied
  by a two-line inline script before the CSS, so there is no flash.
- `static/app.css`, `static/app.js`; the old `style.css` is gone.

## 2. Form and live preview

Status: done (2026-11-16)

- Debounced preview update; URL kept in sync with the form so it can be
  shared.
- Download buttons for SVG and PNG, file name from the text.
- Core warnings shown next to the preview.
- Readable side text: checkbox, and a font selection from `/api/fonts` shown
  when it is on, with the design's default preselected.

Done:

- Preview and `/api/render-info` (size, modules, warnings, licences) are
  fetched 250 ms after the last change; requests that are overtaken are
  dropped. The address bar is kept in sync (`history.replaceState`).
- Without JavaScript the page is a plain GET form with an "Update preview"
  button; the upload needs JavaScript.

## 3. Design picker

Status: done (2026-11-16)

- Designs with title and small preview, from `/api/designs`.
- Second selection for the colour scheme, shown only when the design has
  schemes, with colour swatches; main scheme preselected.

Done:

- Default design first. Changing the design rebuilds the swatches from
  `/api/designs` before the preview is updated, so no stale scheme is sent.

## 4. Icon picker with search and upload

Status: done (2026-11-16)

- Search field over all sources, source filter, grid of results with
  `/icons/...` previews in the current design's colour.
- Upload of an own SVG, with the limits from the config; preview via POST.

Done:

- Live search via `/api/icons` (no-JS: search button, hits rendered by the
  server). Choices "Design" and "None", the current icon is kept in the grid.
- Upload: preview and downloads are posted as `multipart/form-data`; "Copy
  link" says that the link does not carry the uploaded icon.

## 5. Caching

Status: done (2026-11-16)

- The JSON endpoints are built in earlier units (`/api/licences` 0001,
  `/api/designs` and previews 0003, `/api/icons` and icons 0004,
  `/api/fonts` 0005); this unit uses them.
- Cache headers for icons, previews and rendered images (output is
  deterministic).

Done:

- `ETag` (hash of the output) and `Cache-Control: public` on rendered images
  (1 hour), design previews (1 hour) and icons (1 day); conditional requests
  get 304.

## 6. Help page, licences page and footer

Status: done (2026-11-16)

- How to use, what the designs are for, printing and laser cutting hints.
- Licence box under the preview with copyable attribution; checkbox "licence
  info in file" (on by default); licences page.
- Footer: version, source, link to licences.

Done:

- Help rewritten: making a code, options, printing and laser cutting,
  licences, CLI and source. The licences page also lists the fonts of the
  font directories.

## 7. Deployment docs and example config

Status: done (2026-11-16)

- Example config file and a systemd unit or container file for a WSGI
  server.

Done:

- [examples/config.toml](../examples/config.toml),
  [examples/wyltkm.service](../examples/wyltkm.service) (gunicorn, hardened
  systemd unit), steps in [web.md](../web.md), "Deployment".
- Checked in headless Chromium with a scripted run (Playwright over CDP,
  outside the repository): typing, design and scheme change, icon search and
  choice, side text, upload with download, error and recovery, theme switch,
  no-JS form, phone layout. Not part of the test suite, which has no
  browser.

## Also changed in this unit

- `attraktor-bw` is now the scheme `bw` of `attraktor` (schemes `colour`,
  the default, and `bw`). Schemes may set `default_icon`, since the black
  and white scheme uses the mono logo while the colour scheme uses the colour
  logo. Images are unchanged.
- In the same way `38c3-light` and `38c3-lighter` became the schemes `light`
  and `lighter` of `38c3` (default `pilowlava`). Schemes may set fonts in a
  `fonts` table (`top`, `bottom`, `side`). The web form shows schemes as
  chips with a colour dot and the name, since colour swatches cannot tell
  font schemes apart.
- Icon browser: a dialog in the page with all icons, search, sources,
  folders and loading while scrolling; without JavaScript the page
  `/icons/browse`. New `/api/icons/browse`, folders in `/api/icon-sources`,
  `IconSource.folders()`, `IconRegistry.find()`. Icon tiles show the design's
  background. Font Awesome alias files without metadata are left out (2163
  instead of 2883 icons, no duplicates). `<switch>` is now handled (ten Carbon
  icons failed before); a test normalises every built-in icon. Icon zips stay
  open: reading the zip's table of contents for every icon made that test
  take about a minute, now the whole suite runs in about 25 s.
- 40c3 got a scheme `bw` (black on white) for engraving.
