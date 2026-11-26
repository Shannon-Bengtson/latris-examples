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

## This repo is public

Everything here is public: on GitHub, and the gallery on latris.app. Never add business or sensitive information: go-to-market or growth
strategy, pricing, revenue, customers, sales conversations or trial
participants, competitive positioning, the founder's personal or admin
details, internal infrastructure (server addresses, how deploys reach them,
where secrets are kept), secrets or tokens, or the private app's code and
internal plans.
Those live in the private app repo. If a change seems to need them, write only
the engineering or user-facing part, or ask the founder. Commit messages and
pull-request text are public too.
