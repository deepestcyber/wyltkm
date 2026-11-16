# Development plans

This directory tracks planned and ongoing work. We have no ticket system;
these files are where we plan and follow progress. Each unit of work has one
file with its parts and their progress.

## Naming

`NNNN-short-name-state.md`

- `NNNN`: zero-padded, strictly increasing number, never reused. It gives the
  order of the units.
- `short-name`: kebab-case, e.g. `core-split`.
- `state`: `planned` before work starts, `active` while work is ongoing,
  `completed` when done. On a change of state the file is renamed; number and
  name stay the same.

Example: `0001-core-split-completed.md` becomes `0001-core-split-completed.md`.

## Content

- A short introduction with links to the relevant docs.
- An overview table of the parts with their status: `open`, `in progress` or
  `done`.
- One section per part with status, goal and, once done, what was built and
  notes worth keeping.
- Open questions, until they are answered.

Update the file as part of the work: a part is not done until its status and
notes are updated. When a part changes how things work, update the general
docs in [../](../) in the same change.

## Units

| # | Unit | State |
| --- | --- | --- |
| 0001 | [Core split](0001-core-split-completed.md) | completed |
| 0002 | [Configuration and fonts](0002-config-and-fonts-completed.md) | completed |
| 0003 | [Designs](0003-designs-completed.md) | completed |
| 0004 | [Icon sources](0004-icon-sources-completed.md) | completed |
| 0005 | [Readable side text](0005-side-text-completed.md) | completed |
| 0006 | [Web rework](0006-web-rework-planned.md) | planned |
