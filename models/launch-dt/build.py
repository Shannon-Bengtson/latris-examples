"""Build the Launch, license, or do nothing example model.

Applies spec.yaml (substrate, context, sources), types the tree, prices the
branches and payoffs with provenance, and names the shared uncertainty so
the value of information is priced once. Then records the showcase
analysis: the best strategy by expected value, the EVPI on demand, and the
probability at which the answer flips.

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
latris("project", "choose", "decision_tree", "--why",
       "A one-off choice under one dominant uncertainty; the committee wants expected values "
       "and the price of finding out demand before committing.")

latris("dt", "settings", "--objective", "maximise", "--units", "$k")

# ── Node types ───────────────────────────────────────────────────────
latris("dt", "element", "Strategy", "decision")
latris("dt", "element", "Demand if launched", "chance")
latris("dt", "element", "Demand if licensed", "chance")
for terminal in ("Launched, high demand", "Launched, low demand",
                 "Licensed, high demand", "Licensed, low demand", "Do nothing"):
    latris("dt", "element", terminal, "terminal")

# ── Decision branch labels ───────────────────────────────────────────
latris("dt", "branch", "Strategy -> Demand if launched", "--label", "Launch")
latris("dt", "branch", "Strategy -> Demand if licensed", "--label", "License")
latris("dt", "branch", "Strategy -> Do nothing", "--label", "Do nothing")

# ── Chance branches: the same demand uncertainty under both choices ──
# The sales team's estimate from trial conversions; not yet validated.
latris("dt", "branch", "Demand if launched -> Launched, high demand",
       "--label", "High demand", "--probability", "0.4",
       "--origin", "human-elicited", "--unverified",
       "--notes", "Sales team estimate from pilot conversions.")
latris("dt", "branch", "Demand if launched -> Launched, low demand",
       "--label", "Low demand", "--probability", "0.6",
       "--origin", "human-elicited", "--unverified",
       "--notes", "Complement of the high-demand estimate.")
latris("dt", "branch", "Demand if licensed -> Licensed, high demand",
       "--label", "High demand", "--probability", "0.4",
       "--origin", "human-elicited", "--unverified",
       "--notes", "Same underlying market, same probability.")
latris("dt", "branch", "Demand if licensed -> Licensed, low demand",
       "--label", "Low demand", "--probability", "0.6",
       "--origin", "human-elicited", "--unverified",
       "--notes", "Same underlying market, same probability.")

# Name the shared uncertainty so both chance nodes are priced together
# for the value of information.
latris("dt", "uncertainty", "Demand if launched", "Demand")
latris("dt", "uncertainty", "Demand if licensed", "Demand")

# ── Payoffs ($k, first two years, from the finance model) ───────────
latris("dt", "payoff", "Launched, high demand", "1200",
       "--source", "clemen2013", "--origin", "human-elicited",
       "--notes", "Finance model: launch margins net of launch cost in the upside case.")
latris("dt", "payoff", "Launched, low demand",
       "--source", "clemen2013", "--origin", "human-elicited",
       "--notes", "Launch cost unrecovered in the downside case.", "--", "-400")
latris("dt", "payoff", "Licensed, high demand", "350",
       "--origin", "human-elicited",
       "--notes", "Royalty stream in the upside case — we leave most of the upside with the licensee.")
latris("dt", "payoff", "Licensed, low demand", "150",
       "--origin", "human-elicited",
       "--notes", "The royalty floor protects the downside.")
latris("dt", "payoff", "Do nothing", "0",
       "--origin", "human-direct", "--notes", "Walk away clean.")

latris("assumption", "add", "Payoffs are two-year profit in $k; risk attitude is neutral.",
       "--rationale", "The committee asked for expected values, not utility-weighted ones.",
       "--target", "Strategy")

latris("dt", "check")

# ── The showcase analysis (recorded for the report) ──────────────────
latris("dt", "analyse")

latris("finding", "add",
       "Launch edges out license on expected value, but the best estimate of high-demand "
       "probability sits within a hair of the point where the answer flips.",
       "--category", "inference", "--target", "Strategy",
       "--detail", "Launch's expected value beats license by about $10k, and the switch-over "
                   "probability is just under the sales team's 0.4 estimate — the choice is fragile.")
latris("finding", "add",
       "Perfect information on demand is worth roughly $330k — that is the ceiling on what the "
       "market research under debate could possibly be worth.",
       "--category", "recommendations", "--target", "Demand if launched",
       "--detail", "EVPI prices the uncertainty both choices share; any research costing more than "
                   "the EVPI destroys value regardless of quality.")
