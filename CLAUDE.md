# CLAUDE.md

Notes for AI coding agents working in this repository. Start at
[README.md](./README.md): the model folders and how the gallery is built.

## Publishing is the founder's call

A push or merge to `main` runs `build-gallery.yml`, which rebuilds every model
and pushes the result to latris-site, which publishes it to latris.app. Work on
a branch and open a pull request; don't push or merge to `main` until the
founder says to. After a latris release, bumping `requirements.txt` is a pull
request too.
