"""Build the A fishery under quota pressure example model.

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
latris("project", "select-models", "sd")
latris("project", "choose", "sd", "--why", "The question is about dynamics over time: stocks, harvests and the feedback between them.")

# TODO: parameterise (SD roles, equations, initial values; scenarios for quota options; simulate + monte-carlo + loop dominance) and record the showcase analyses.
