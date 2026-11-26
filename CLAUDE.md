# CLAUDE.md

Notes for AI coding agents working in this repository. Start at
[README.md](./README.md): the model folders and how the gallery is built.

## How this repo connects to the others

- **latris** (public library): `requirements.txt` pins its version. Bump it
  after a latris release.
- **latris-app** (private): `latris-app-ref.txt` pins the app commit whose
  `latris_present` renders the report, explorer and story pages. CI installs
  it with the `GALLERY_PAT` secret; bump the ref when those pages change.
- **latris-site** (public): CI commits the built gallery into its
  `examples/gallery/`, and GitHub Pages serves it at latris.app.

## Publishing is the founder's call

A push or merge to `main` runs `build-gallery.yml`, which rebuilds every model
and pushes the result to latris-site, which publishes it to latris.app. Work on
a branch and open a pull request; don't push or merge to `main` until the
founder says to. After a latris release, bumping `requirements.txt` is a pull
request too.
