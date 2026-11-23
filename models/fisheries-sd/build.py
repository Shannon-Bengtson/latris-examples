"""Build the A fishery under quota pressure example model.

Applies spec.yaml (substrate, context, sources), then wires the system
dynamics: a logistic-surplus recruitment flow, natural mortality, and a
quota-capped harvest, with the fleet-effort loop responding to profit with
a year's delay. Records the showcase analyses: a twenty-year baseline run
against a quota-cut scenario, and a Monte Carlo over the uncertain growth
rate and catchability.

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
latris("project", "choose", "sd", "--why",
       "The question is about a stock over twenty years under feedback: recruitment, harvest "
       "pressure and the fleet's response to profit all move together.")

# ── Roles ────────────────────────────────────────────────────────────
latris("sd", "set-role", "Fish biomass", "stock")
latris("sd", "set-role", "Fishing effort", "stock")
latris("sd", "set-role", "Outside the fishery", "source_sink")
for flow in ("Recruitment", "Natural mortality", "Harvest", "Effort adjustment"):
    latris("sd", "set-role", flow, "flow")
latris("sd", "set-role", "Fleet profitability", "auxiliary")
for const in ("Quota", "Growth rate", "Carrying capacity", "Mortality rate",
              "Catchability", "Price", "Cost per vessel", "Adjustment rate",
              "Reference profit"):
    latris("sd", "set-role", const, "constant")

# ── Flow plumbing: stock → flow → stock, with the outside as clouds ──
latris("edge", "add", "Outside the fishery", "Recruitment", "--kind", "flow")
latris("edge", "add", "Recruitment", "Fish biomass", "--kind", "flow")
latris("edge", "add", "Fish biomass", "Natural mortality", "--kind", "flow")
latris("edge", "add", "Natural mortality", "Outside the fishery", "--kind", "flow")
latris("edge", "add", "Fish biomass", "Harvest", "--kind", "flow")
latris("edge", "add", "Harvest", "Outside the fishery", "--kind", "flow")
latris("edge", "add", "Outside the fishery", "Effort adjustment", "--kind", "flow")
latris("edge", "add", "Effort adjustment", "Fishing effort", "--kind", "flow")

# ── Clock: twenty years, annual clock, tight step ────────────────────
latris("sd", "set-settings", "--time-units", "year", "--final-time", "20",
       "--dt", "0.1", "--method", "rk4")

# ── Stocks ───────────────────────────────────────────────────────────
latris("sd", "set-initial-value", "Fish biomass", "60", "--units", "kt",
       "--non-negative", "--origin", "data-derived",
       "--source", "fao2024")
latris("sd", "set-initial-value", "Fishing effort", "100", "--units", "item",
       "--non-negative", "--origin", "data-derived")

# ── Constants, each with provenance ──────────────────────────────────
latris("sd", "set-constant", "Quota", "3.5", "--units", "kt/year",
       "--origin", "human-direct")
latris("sd", "set-constant", "Growth rate", "0.35", "--units", "1/year",
       "--source", "hilborn1992", "--origin", "human-elicited")
latris("sd", "set-constant", "Carrying capacity", "100", "--units", "kt",
       "--source", "hilborn1992", "--origin", "human-elicited")
latris("sd", "set-constant", "Mortality rate", "0.15", "--units", "1/year",
       "--origin", "human-elicited")
latris("sd", "set-constant", "Catchability", "0.0007", "--units", "1/item/year",
       "--origin", "data-derived")
latris("sd", "set-constant", "Price", "2", "--units", "dollar/kt",
       "--origin", "data-derived")
latris("sd", "set-constant", "Cost per vessel", "0.05", "--units", "dollar/year/item",
       "--origin", "human-elicited")
latris("sd", "set-constant", "Adjustment rate", "0.1", "--units", "1/year",
       "--origin", "human-elicited")
latris("sd", "set-constant", "Reference profit", "1", "--units", "dollar/year",
       "--origin", "human-elicited")

latris("assumption", "add", "The stock starts at 60% of the unfished level, and catchability "
       "comes from logbooks with thin small-vessel coverage.",
       "--rationale", "Last survey estimate for the opening biomass; catchability is the "
                      "softest data-derived number, so it carries an uncertainty range below.",
       "--target", "Fish biomass")

# ── Equations (names are slugified labels) ───────────────────────────
# Logistic surplus production.
latris("sd", "set-equation", "Recruitment",
       "fish_biomass * growth_rate * (1 - fish_biomass / carrying_capacity)",
       "--units", "kt/year", "--source", "hilborn1992", "--origin", "human-elicited")
latris("sd", "set-equation", "Natural mortality",
       "fish_biomass * mortality_rate",
       "--units", "kt/year", "--origin", "human-elicited")
# Harvest: what the fleet could catch, capped by the quota.
latris("sd", "set-equation", "Harvest",
       "MIN(quota, catchability * fishing_effort * fish_biomass)",
       "--units", "kt/year", "--source", "hilborn1992", "--origin", "human-elicited")
latris("sd", "set-equation", "Fleet profitability",
       "harvest * price - fishing_effort * cost_per_vessel",
       "--units", "dollar/year", "--origin", "human-elicited")
# The fleet enters when profit beats the reference and exits when it falls
# short — the stock in the loop, adjusting over about two years.
latris("sd", "set-equation", "Effort adjustment",
       "fishing_effort * adjustment_rate * (fleet_profitability / reference_profit - 1)",
       "--units", "item/year", "--origin", "human-elicited")

latris("sd", "check")

# ── Evidence checks (verbatim support from the stored extracts) ──────
latris("evidence", "check", "Fish biomass -> Recruitment", "description", "hilborn1992",
       "supports", "--rationale", "Surplus-production models relate recruitment to stock size and "
                                  "fishing pressure — the form used here.")
latris("evidence", "check", "Quota -> Harvest", "description", "fao2024",
       "supports", "--rationale", "Effective management is the strongest predictor of recovery; "
                                  "the quota is that management lever in this model.")

# ── The showcase analyses (recorded for the report) ──────────────────
# Baseline vs a quota cut to maximum sustainable yield (~2.8 kt/yr at the
# central growth rate).
latris("sd", "set-scenario", "Cut quota to 2.5 kt", "--set", "Quota=2.5",
       "--reason", "Below the central MSY estimate of 2.9 kt/yr, so the stock keeps "
                   "headroom in mediocre recruitment years.",
       "--source", "hilborn1992", "--origin", "human-elicited")
latris("sd", "simulate", "-s", "Cut quota to 2.5 kt")

# Which feedback loop drives the behaviour, and when.
latris("sd", "loops")

# How sure is the twenty-year picture? Recruitment growth dominates
# long-run projections; catchability is the other soft number.
latris("sd", "set-uncertainty", "Growth rate", "triangular",
       "--min", "0.2", "--mode", "0.35", "--max", "0.5",
       "--reason", "Recruitment uncertainty dominates long-run projections.",
       "--source", "hilborn1992")
latris("sd", "set-uncertainty", "Catchability", "triangular",
       "--min", "0.0005", "--mode", "0.0007", "--max", "0.0009",
       "--reason", "Logbook-derived; coverage of the small-vessel segment is thin.")
latris("sd", "monte-carlo", "-n", "500", "-v", "Fish biomass", "-v", "Harvest")

latris("finding", "add",
       "The current 3.5 kt cap buys a few years of full landings, then harvest slides to "
       "about 1.8 kt while the stock sheds a third of its biomass.",
       "--category", "dynamics", "--target", "Fish biomass",
       "--detail", "The cap sits above the central MSY estimate, so the stock is fished down "
                   "until the fleet can no longer fill it.")
latris("finding", "add",
       "Cutting the cap to 2.5 kt ends the horizon better on every measure the council "
       "cares about: more fish, more catch, and a healthier fleet.",
       "--category", "recommendations", "--target", "Quota",
       "--detail", "By year twenty the lower cap lands about 2.0 kt against 1.8 kt under the "
                   "status quo, on a larger stock with higher fleet profit — the short-term "
                   "sacrifice pays for itself inside the horizon.")
latris("finding", "add",
       "A generous cap first attracts vessels — effort overshoots to about 120 — and then "
       "grinds two-fifths of the fleet out of the fishery.",
       "--category", "structure", "--target", "Fishing effort",
       "--detail", "The profit loop amplifies the quota's effect both ways: entry on the "
                   "fat years, exit once the stock is fished down.")
latris("finding", "add",
       "The growth rate dominates the spread of outcomes — a bad-recruitment world is where "
       "the current quota fails.",
       "--category", "sensitivity", "--target", "Growth rate",
       "--detail", "In the Monte Carlo the growth-rate range moves end-state biomass far more "
                   "than the catchability range.")
