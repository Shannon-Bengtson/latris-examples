"""Build the Launch, license, or do nothing example model.

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
latris("project", "select-models", "decision_tree")
latris("project", "choose", "decision_tree", "--why", "A choice under uncertainty with priced outcomes: the tree rolls back to the best strategy.")

# TODO: parameterise (branches with sourced probabilities; payoffs; dt analyse (EV, EVPI, flip probability); PSA) and record the showcase analyses.
