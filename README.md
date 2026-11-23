# latris-examples

The example models behind the [latris.app](https://latris.app) gallery: ten small
but carefully built models across health, environment, policy, security, business,
engineering and development — one per strength of [latris](https://github.com/Shannon-Bengtson/latris).

Each model is a folder under `models/` that can be rebuilt from scratch:

```
models/<slug>/
  model.yaml   # manifest: title, domain, formalisms, question, story/report/explorer config
  spec.yaml    # the substrate: context, factors, links, sources (real citations)
  build.py     # python build.py <project-root> — parameters, evidence checks, analyses
```

`tools/build_all.py` runs every model end to end — build, analyses, interpretation —
then renders three self-contained artifacts per model with the app's
`latris_present`: the hosted report page, the interactive explorer, and the
scrollytelling story. It writes them to `dist/<slug>/` plus a `dist/gallery.json`
index that the website consumes.

## Running locally

```bash
pip install -r requirements.txt
pip install -e ../latris-app          # for the rendered artifacts (private repo)
python tools/build_all.py             # every live model
python tools/build_all.py --models sepsis-bn --keep-work
```

Stories are AI-written (plan → approve → write, with grounding checks). Without a
provider key the story step is skipped:

```bash
export ANTHROPIC_API_KEY=...          # or another provider latris supports
```

Models marked `status: draft` in their manifest are skipped unless `--include-drafts`.

## CI (auto-publish)

`.github/workflows/build-gallery.yml` rebuilds the gallery on every push to `main`
(and on a `repository_dispatch: latris-release` ping), then commits the artifacts
to `latris-site` under `examples/gallery/`, which GitHub Pages deploys. Secrets:

- `ANTHROPIC_API_KEY` — story generation
- `GALLERY_PAT` — a fine-grained token with read on `latris-app` (to install
  `latris_present`) and read/write on `latris-site` (to publish)

After a latris release: bump `requirements.txt`, push, done — the gallery rebuilds.

## The models

| Slug | Domain | Formalism | Question |
|---|---|---|---|
| `sepsis-bn` | Health | Bayesian network | How likely is a deteriorating ward patient to develop sepsis? |
| `fisheries-sd` | Environment | System dynamics | Can the fishery stay sustainable under current quotas? |
| `air-quality-dag` | Environment / health | DAG + effect estimation | How much do traffic restrictions improve respiratory health? |
| `policy-fcm` | Policy | Fuzzy cognitive map | What does an EV subsidy do to the regional transport system? |
| `hospital-mcda` | Public sector | MCDA | Which site should the new hospital go on? |
| `intrusion-ach` | Security | Analysis of competing hypotheses | What explains the unusual activity on the network? |
| `launch-dt` | Business | Decision tree | Launch, license, or do nothing? |
| `screening-markov` | Health economics | Markov cohort | Is a screening programme worth its cost? |
| `mentoring-toc` | Development | Theory of change + process tracing | Does the mentoring programme raise school completion? |
| `cooling-ft` | Engineering | Fault tree + Monte Carlo | How likely is a loss of cooling, and what drives it? |

Numbers in these models are illustrative; the sources are real and cited so the
evidence machinery (attachments, checks, contested links) shows in the reports.
