"""Build the Does mentoring raise school completion? example model.

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
latris("project", "select-models", "theory_of_change")
latris("project", "choose", "theory_of_change", "--why", "The programme's theory is a chain of claims; each link gets its evidence and its tests.")

# TODO: parameterise (levels; assumptions per link; priors and tests (process tracing); toc trace; impact (ITS/DiD) on a synthetic dataset) and record the showcase analyses.
