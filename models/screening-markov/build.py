"""Build the Is the screening programme worth its cost? example model.

Applies spec.yaml (substrate, context, sources), then parameterises the
formalism and runs the analyses the gallery shows.

Usage: python build.py <project-root>
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
HERE = Path(__file__).resolve().parent


def latris(*args: str, input: str | None = None) -> None:
    print("$ latris", " ".join(args))
    subprocess.run(["latris", *args], cwd=ROOT, input=input, text=True, check=True)


spec = (HERE / "spec.yaml").read_text(encoding="utf-8")
latris("build", "--spec", "-", input=spec)
latris("project", "select-models", "markov")
latris("project", "choose", "markov", "--why", "A cohort moving between health states over years, compared under two strategies on cost and QALYs.")

# TODO: parameterise (states, transition probabilities per strategy with sources; rewards; markov analyse (ICER); PSA + acceptability curve) and record the showcase analyses.
