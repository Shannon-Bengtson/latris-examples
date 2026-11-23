"""Build the An EV subsidy in the regional transport system example model.

Applies spec.yaml (substrate, context, sources), sets the signed edge
weights elicited in the departmental workshop, then runs the showcase
analyses: a qualitative propagation trace, the baseline steady state, and
the steady state with the subsidy clamped on — the knock-on effects the
single-issue briefings missed.

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
latris("project", "choose", "fcm", "--why",
       "The departments disagree because each sees one edge of the system; a stakeholder "
       "map with signed weights lets the whole council watch the knock-ons settle.")

# ── Edge weights from the departmental workshop (−1..+1) ─────────────
latris("fcm", "set-weight", "EV subsidy -> EV adoption", "0.8")
latris("fcm", "set-weight", "EV adoption -> Tailpipe emissions", "--", "-0.8")
latris("fcm", "set-weight", "Tailpipe emissions -> Air quality", "--", "-0.8")
latris("fcm", "set-weight", "Air quality -> Respiratory illness", "--", "-0.7")
latris("fcm", "set-weight", "EV adoption -> Congestion", "0.3")
latris("fcm", "set-weight", "EV adoption -> Household transport costs", "--", "-0.4")
latris("fcm", "set-weight", "EV adoption -> Electricity demand", "0.5")
# The feedback: congestion costs households, and household costs temper uptake.
latris("fcm", "set-weight", "Congestion -> Household transport costs", "0.5")
latris("fcm", "set-weight", "Household transport costs -> EV adoption", "--", "-0.3")

latris("assumption", "add", "Edge weights are workshop judgements on a −1..+1 scale, "
       "not fitted parameters.",
       "--rationale", "Elicited per the participatory-mapping method; the map explores "
                      "scenarios, it does not forecast magnitudes.",
       "--target", "EV subsidy -> EV adoption")

# ── Evidence: the methods behind the map and its inference ───────────
latris("evidence", "add", "EV subsidy", "description", "kosko1986")
latris("evidence", "check", "EV subsidy", "description", "kosko1986",
       "supports", "--rationale", "Signed weighted concepts combined by matrix inference to a "
                                  "fixed point — Kosko's formulation is what the runs below do.")
latris("evidence", "check", "Congestion -> Household transport costs", "description", "gray2015",
       "supports", "--rationale", "Stakeholder-elicited maps support scenario exploration where "
                                  "data are scarce — the workshop this edge came from.")

# ── The showcase analyses (recorded for the report) ──────────────────
# Qualitative trace: every path the subsidy's influence travels.
latris("analyse", "propagate", "EV subsidy")

# Steady state without the policy, then with the subsidy clamped on.
latris("fcm", "infer", "--clamp", "EV subsidy=0")
latris("fcm", "infer", "--clamp", "EV subsidy=1.0")

latris("finding", "add",
       "With the subsidy clamped on, the map settles with emissions and respiratory illness "
       "down but congestion and electricity demand up — the trade-off the single-issue "
       "briefings missed.",
       "--category", "dynamics", "--target", "EV subsidy",
       "--detail", "The clamped run prices the whole system at once: the environment department's "
                   "gain and the transport department's cost appear in the same steady state.")
latris("finding", "add",
       "The congestion-to-household-cost feedback tempers adoption but does not reverse it — "
       "the map still settles at a new fixed point.",
       "--category", "structure", "--target", "Household transport costs",
       "--detail", "Congestion raises household costs, which damp uptake; the negative loop "
                   "stabilises the system instead of undoing the policy.")
