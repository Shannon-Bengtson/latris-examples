"""Build the Loss of cooling at the data centre example model.

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
latris("project", "select-models", "fault_tree")
latris("project", "choose", "fault_tree", "--why", "One undesired top event decomposed through gates to the basic events that cause it.")

# TODO: parameterise (event types, gates (and/or/vote); probabilities with sources; ft analyse (cut sets, importance); uncertainty + monte-carlo) and record the showcase analyses.
