# Web rework

Status: planned

A web interface that is easy to use and looks good: live preview, design
picker, icon search and upload, clean download. Server-rendered, small vanilla
JavaScript, no build step.

Background: [web.md](../web.md).

Status values: `open`, `in progress`, `done`.

| # | Part | Status |
| --- | --- | --- |
| 1 | Visual direction and layout | open |
| 2 | Form and live preview | open |
| 3 | Design picker | open |
| 4 | Icon picker with search and upload | open |
| 5 | Caching | open |
| 6 | Help page, licences page and footer | open |
| 7 | Deployment docs and example config | open |

## 1. Visual direction and layout

Status: open

- Agree on a look (sketch first): two columns on wide screens, preview on top
  on phones, works without JavaScript.
- Dark and light theme.

## 2. Form and live preview

Status: open

- Debounced preview update; URL kept in sync with the form so it can be
  shared.
- Download buttons for SVG and PNG, file name from the text.
- Core warnings shown next to the preview.
- Readable side text: checkbox, and a font selection from `/api/fonts` shown
  when it is on, with the design's default preselected.

## 3. Design picker

Status: open

- Designs with title and small preview, from `/api/designs`.
- Second selection for the colour scheme, shown only when the design has
  schemes, with colour swatches; main scheme preselected.

## 4. Icon picker with search and upload

Status: open

- Search field over all sources, source filter, grid of results with
  `/icons/...` previews in the current design's colour.
- Upload of an own SVG, with the limits from the config; preview via POST.

## 5. Caching

Status: open

- The JSON endpoints are built in earlier units (`/api/licences` 0001,
  `/api/designs` and previews 0003, `/api/icons` and icons 0004,
  `/api/fonts` 0005); this unit uses them.
- Cache headers for icons, previews and rendered images (output is
  deterministic).

## 6. Help page, licences page and footer

Status: open

- How to use, what the designs are for, printing and laser cutting hints.
- Licence box under the preview with copyable attribution; checkbox "licence
  info in file" (on by default); licences page.
- Footer: version, source, link to licences.

## 7. Deployment docs and example config

Status: open

- Example config file and a systemd unit or container file for a WSGI
  server.
