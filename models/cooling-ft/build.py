"""Build the Loss of cooling at the data centre example model.

Applies spec.yaml (substrate, context, sources), types the tree, sets the
gates — including the 2-out-of-3 vote on the shared power supplies — and
prices the leaves with per-value provenance. Then records the showcase
analyses: cut sets and importance rankings, and a Monte Carlo over the
uncertain probabilities.

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
latris("project", "choose", "fault_tree", "--why",
       "One undesired top event decomposed through gates to the basic events that cause it.")

# ── Event types ──────────────────────────────────────────────────────
latris("ft", "event", "Loss of cooling", "top_event")
latris("ft", "event", "Both pumps fail", "intermediate_event")
latris("ft", "event", "Pump A fails", "intermediate_event")
latris("ft", "event", "Pump B fails", "intermediate_event")
latris("ft", "event", "Power lost", "intermediate_event")
latris("ft", "event", "Pump A mechanical failure", "basic_event")
latris("ft", "event", "Pump B mechanical failure", "basic_event")
latris("ft", "event", "Supply 1 fails", "basic_event")
latris("ft", "event", "Supply 2 fails", "basic_event")
latris("ft", "event", "Supply 3 fails", "basic_event")
# The shared controller is not decomposed further — priced as one event.
latris("ft", "event", "Control fault", "undeveloped_event")

# ── Gates ────────────────────────────────────────────────────────────
latris("ft", "gate", "Loss of cooling", "or")
latris("ft", "gate", "Both pumps fail", "and")
latris("ft", "gate", "Pump A fails", "or")
latris("ft", "gate", "Pump B fails", "or")
# Three supplies, any two can carry the load: power is lost when two fail.
latris("ft", "gate", "Power lost", "vote", "-k", "2")

# ── Leaf probabilities (one-year exposure), each with provenance ─────
latris("ft", "probability", "Pump A mechanical failure", "0.02",
       "--source", "oreda2015", "--origin", "human-elicited",
       "--notes", "Generic centrifugal-pump failure rate, one-year exposure; illustrative of OREDA ranges.")
latris("ft", "probability", "Pump B mechanical failure", "0.02",
       "--source", "oreda2015", "--origin", "human-elicited",
       "--notes", "Same duty and vintage as pump A.")
latris("ft", "probability", "Supply 1 fails", "0.02",
       "--source", "ieee493", "--origin", "human-elicited",
       "--notes", "Generic industrial supply unavailability, Gold Book order of magnitude.")
latris("ft", "probability", "Supply 2 fails", "0.02",
       "--source", "ieee493", "--origin", "human-elicited",
       "--notes", "Same supply class as Supply 1.")
latris("ft", "probability", "Supply 3 fails", "0.03",
       "--source", "ieee493", "--origin", "human-elicited",
       "--notes", "Older supply on a longer run; slightly higher unavailability.")
latris("ft", "probability", "Control fault", "0.002",
       "--origin", "human-elicited",
       "--notes", "Workshop estimate; nobody has pulled the controller logs. The number to verify.")

latris("assumption", "add", "Supply failures are independent of each other.",
       "--rationale", "Separate feeds and switchgear; common-cause supply failures are not yet priced.",
       "--target", "Power lost")

latris("ft", "check")

# ── Evidence checks (verbatim support from the stored extracts) ──────
latris("evidence", "check", "Both pumps fail -> Loss of cooling", "description", "nasa2002",
       "supports", "--rationale", "The handbook decomposes the top event through AND/OR gates; minimal cut sets reveal what defeats the redundant pumps.")
latris("evidence", "check", "Supply 1 fails -> Power lost", "description", "iec61025",
       "supports", "--rationale", "IEC 61025 defines the k-out-of-n voting gate used for the three supplies.")

# ── The showcase analyses (recorded for the report) ──────────────────
# Exact top-event probability, minimal cut sets, single points of failure,
# and importance rankings.
latris("ft", "analyse")

# How sure is the headline number when the leaf probabilities are ranges?
latris("ft", "uncertainty", "Pump A mechanical failure", "lognormal",
       "--median", "0.02", "--error-factor", "3",
       "--reason", "Generic data, not site-specific", "--source", "oreda2015")
latris("ft", "uncertainty", "Supply 1 fails", "lognormal",
       "--median", "0.02", "--error-factor", "3",
       "--reason", "Generic data, not site-specific", "--source", "ieee493")
latris("ft", "uncertainty", "Supply 2 fails", "lognormal",
       "--median", "0.02", "--error-factor", "3",
       "--reason", "Generic data, not site-specific", "--source", "ieee493")
latris("ft", "uncertainty", "Supply 3 fails", "lognormal",
       "--median", "0.03", "--error-factor", "3",
       "--reason", "Generic data, not site-specific", "--source", "ieee493")
latris("ft", "uncertainty", "Control fault", "lognormal",
       "--median", "0.002", "--error-factor", "5",
       "--reason", "Unverified workshop estimate; widest range of the set")
latris("ft", "monte-carlo", "--runs", "2000")

latris("finding", "add",
       "Loss of cooling is driven by single events that bypass the pump redundancy — "
       "the shared power supply and the control fault — not by the double mechanical failure "
       "the second pump was bought to prevent.",
       "--category", "inference", "--target", "Loss of cooling",
       "--detail", "The minimal cut sets include two single-event cut sets (Power lost, Control fault) "
                   "alongside the two-event mechanical combination.")
latris("finding", "add",
       "The unverified control-fault estimate is the biggest driver of the spread in the "
       "top-event probability.",
       "--category", "sensitivity", "--target", "Control fault",
       "--detail", "In the Monte Carlo, the widest error factor sits on the least verified number; "
                   "pulling the controller logs would shrink the band most.")
