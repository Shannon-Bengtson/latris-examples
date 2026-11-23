"""Build the Traffic restrictions and respiratory health example model.

Applies spec.yaml (substrate, context, sources), generates a synthetic
area-level dataset with a known causal structure (restrictions cut
emissions; deprivation confounds zone placement), then runs the showcase
analyses: the backdoor adjustment set the DAG demands, a testable
d-separation implication, and adjusted effect estimates beside the naive
unadjusted association.

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
latris("project", "select-models", "dag")
latris("project", "choose", "dag", "--why",
       "The evidence is observational, so the fight is over confounding: the DAG says "
       "exactly what must be adjusted before any number is believed.")

# ── A synthetic area-level dataset with a known structure ────────────
# 400 areas. Restrictions cut emissions by 18 units; pollution raises
# admissions. Zone placement tracks deprivation — the confounder the
# naive before/after comparison trips over.
import numpy as np

rng = np.random.RandomState(42)
n = 400
deprivation = rng.normal(50, 15, n).clip(5, 95)
p_zone = 1 / (1 + np.exp(-(deprivation - 45) / 8))
restrictions = (rng.uniform(size=n) < p_zone).astype(int)
smoking = 12 + 0.25 * deprivation + rng.normal(0, 3, n)
weather = rng.normal(50, 10, n).clip(10, 90)
emissions = 60 - 18 * restrictions + rng.normal(0, 6, n)
pollution = 0.6 * emissions + 0.5 * weather + rng.normal(0, 4, n)
admissions = (30 + 0.35 * pollution + 0.12 * deprivation
              + 0.5 * smoking + 0.08 * weather + rng.normal(0, 3, n))

csv_path = ROOT / "admissions.csv"
with csv_path.open("w", encoding="utf-8") as fh:
    fh.write("Socioeconomic deprivation,Traffic restrictions,Smoking prevalence,"
             "Weather and season,Vehicle emissions,Air pollution,"
             "Respiratory hospital admissions\n")
    for row in zip(deprivation, restrictions, smoking, weather,
                   emissions, pollution, admissions):
        fh.write(",".join(f"{v:.3f}" for v in row) + "\n")

latris("data", "add", str(csv_path), "--name", "admissions",
       "--description", "Weekly respiratory admissions per 100k across 400 areas, with the "
                        "confounders the DAG names. Synthetic illustration for the gallery, "
                        "generated with a fixed seed by build.py.")

latris("assumption", "add", "Every common cause of zone placement and admissions is in the DAG "
       "and measured in the data.",
       "--rationale", "This is the exchangeability assumption the adjusted estimate rests on; "
                      "an unmeasured confounder would bias it.",
       "--target", "Traffic restrictions")

# ── Evidence checks (verbatim support from the stored extracts) ──────
latris("evidence", "check", "Air pollution -> Respiratory hospital admissions",
       "description", "who2021", "supports",
       "--rationale", "The 2021 guidelines tighten PM2.5 and NO2 limits on evidence linking "
                      "exposure to respiratory outcomes — the link the estimate sizes.")
latris("evidence", "check", "Vehicle emissions -> Air pollution", "description", "hei2010",
       "supports", "--rationale", "The HEI review ties traffic emissions to roadside "
                                  "concentrations, with exposure assessment the main uncertainty.")

# ── The showcase analyses (recorded for the report) ──────────────────
# What must we adjust for? The DAG answers before any regression runs.
latris("analyse", "adjustment-sets", "Traffic restrictions",
       "Respiratory hospital admissions")

# A testable implication: smoking has no path to zone placement except
# through a collider, so the DAG says they are independent.
latris("analyse", "d-sep", "Smoking prevalence", "Traffic restrictions")

# The headline: the adjusted effect against the naive unadjusted association.
latris("analyse", "estimate", "Traffic restrictions",
       "Respiratory hospital admissions", "--dataset", "admissions")
# Second cut: the pollution dose-response, adjusted as the DAG requires
# (weather confounds this one; deprivation does not).
latris("analyse", "estimate", "Air pollution",
       "Respiratory hospital admissions", "--dataset", "admissions")

latris("finding", "add",
       "Adjusted for deprivation — the backdoor the DAG demands — the zone's effect is "
       "several fewer weekly admissions per 100k; the unadjusted comparison hides most of it.",
       "--category", "inference", "--target", "Traffic restrictions",
       "--detail", "Zone placement tracks deprivation and deprivation drives admissions, so the "
                   "raw contrast credits the zone with areas' underlying risk. Adjusting for "
                   "deprivation recovers the effect operating through emissions and pollution.")
latris("finding", "add",
       "The bias lives on one open backdoor: zone placement tracks deprivation, and "
       "deprivation drives admissions.",
       "--category", "structure", "--target", "Socioeconomic deprivation",
       "--detail", "adjustment-sets names exactly {Socioeconomic deprivation}; smoking and "
                   "weather improve precision but are not confounders here.")
latris("finding", "add",
       "The estimate is causal only under the DAG — an unmeasured common cause of placement "
       "and admissions would still bias it.",
       "--category", "diagnostics", "--target", "Traffic restrictions",
       "--detail", "That is the assumption logged against the model; the DAG makes it explicit "
                   "so the committee can attack it directly.")
