"""Build the An EV subsidy in the regional transport system example model.

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
latris("project", "select-models", "fcm")
latris("project", "choose", "fcm", "--why", "Stakeholders gave qualitative causal strengths; FCM turns them into scenario inference.")

# TODO: parameterise (edge weights; fcm infer baseline; clamp the subsidy; compare steady states) and record the showcase analyses.
