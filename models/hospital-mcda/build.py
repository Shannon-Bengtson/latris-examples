"""Build the Siting the new hospital example model.

Applies spec.yaml (substrate, context, sources), then parameterises the
MCDA: five criteria with explicit scales and swing weights from the board
workshop, and fifteen scores each carrying its own provenance. Records the
showcase analysis: the ranking, criterion contributions, and how far each
weight would have to move before the top choice changes.

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
latris("project", "select-models", "mcda")
latris("project", "choose", "mcda", "--why",
       "A choice between three sites judged on several criteria at once; the board must "
       "show its workings, so weights and scores need visible provenance.")

# ── Options and criteria ─────────────────────────────────────────────
for option in ("Riverside", "North Park", "Old Depot"):
    latris("mcda", "element", option, "option")
for criterion in ("Build cost", "Travel time", "Bed capacity",
                  "Expansion potential", "Community acceptance"):
    latris("mcda", "element", criterion, "criterion")

# ── Criteria: explicit scales first, then swing weights ──────────────
# Weights elicited in the board's March workshop, swing-weighting per the
# ISPOR good-practices report.
latris("mcda", "criterion", "Build cost", "--direction", "lower",
       "--worst", "100", "--best", "50", "--units", "£m", "--weight", "0.30",
       "--source", "thokala2016", "--origin", "human-elicited",
       "--notes", "Board swing weight: moving £100m→£50m matters most to the board.")
latris("mcda", "criterion", "Travel time", "--direction", "lower",
       "--worst", "40", "--best", "15", "--units", "min", "--weight", "0.25",
       "--source", "thokala2016", "--origin", "human-elicited",
       "--notes", "Average peak minutes for the catchment; second-largest swing.")
latris("mcda", "criterion", "Bed capacity", "--direction", "higher",
       "--worst", "300", "--best", "500", "--units", "beds", "--weight", "0.20",
       "--source", "thokala2016", "--origin", "human-elicited",
       "--notes", "Clinical envelope the site can hold.")
latris("mcda", "criterion", "Expansion potential", "--direction", "higher",
       "--worst", "0", "--best", "100", "--units", "index", "--weight", "0.10",
       "--source", "thokala2016", "--origin", "human-elicited",
       "--notes", "Estates index of room to grow; smallest swing.")
latris("mcda", "criterion", "Community acceptance", "--direction", "higher",
       "--worst", "30", "--best", "90", "--units", "%", "--weight", "0.15",
       "--source", "thokala2016", "--origin", "human-elicited",
       "--notes", "Share of consultation respondents in favour.")

# ── Scores: each with where it came from ─────────────────────────────
SCORES = {
    #                cost  travel  capacity  expansion  acceptance
    "Riverside":   (95,    18,     380,       20,        85),
    "North Park":  (70,    28,     450,       80,        55),
    "Old Depot":   (55,    35,     420,       60,        40),
}
PROVENANCE = {
    #                  origin              verified  notes
    "Build cost": ("human-elicited", True, "Quantity surveyor's feasibility estimate, ±10%."),
    "Travel time": ("data-derived", True, "Catchment transport model, average peak minutes."),
    "Bed capacity": ("human-elicited", False, "Clinical planning envelope for the site."),
    "Expansion potential": ("human-elicited", False, "Estates survey, room-to-grow index 0–100."),
    "Community acceptance": ("data-derived", True, "Public consultation survey, % in favour."),
}
for option, values in SCORES.items():
    for criterion, value in zip(PROVENANCE, values):
        origin, verified, notes = PROVENANCE[criterion]
        args = ["--origin", origin, "--notes", notes]
        if verified:
            args.append("--verified")
        latris("mcda", "score", option, criterion, str(value), *args)

latris("mcda", "check")

# ── Evidence: the ISPOR report backs the weighting method ────────────
latris("evidence", "add", "Build cost", "description", "thokala2016")
latris("evidence", "check", "Build cost", "description", "thokala2016",
       "supports", "--rationale", "Good practice is swing weighting on explicit scales with "
                                  "sensitivity analysis before the decision is communicated — "
                                  "exactly the exercise the board ran.")

# ── The showcase analysis (recorded for the report) ──────────────────
latris("mcda", "analyse")

latris("finding", "add",
       "North Park wins; the beloved Riverside site comes last once all five swings are priced.",
       "--category", "inference", "--target", "North Park",
       "--detail", "Riverside's travel-time and acceptance advantages do not cover its build cost "
                   "and cramped expansion at the board's own weights.")
latris("finding", "add",
       "Build cost is the weight to watch: if the board priced the cost swing higher, "
       "the answer would flip to Old Depot.",
       "--category", "sensitivity", "--target", "Build cost",
       "--detail", "The weight-sensitivity table shows how far each swing weight must move before "
                   "the top choice changes; cost has the shortest distance to a flip.")
latris("finding", "add",
       "The margin rests on the two unverified scores — bed capacity and expansion potential.",
       "--category", "diagnostics", "--target", "North Park",
       "--detail", "Costs, travel times and acceptance figures are checked against their sources; "
                   "the planning envelope and estates index are not. Estates should firm those up "
                   "before the choice is announced publicly.")
