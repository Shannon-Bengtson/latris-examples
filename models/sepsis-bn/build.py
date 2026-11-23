"""Build the sepsis-risk Bayesian network (the gallery pilot).

Applies spec.yaml, quantifies the BN with per-table provenance, then records
the analyses the gallery shows: marginals, a predictive and a diagnostic
query, the most likely explanation, parameter sensitivity, and Monte Carlo
uncertainty on the key posterior.

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
latris("project", "select-models", "bn")
latris("project", "choose", "bn", "--why",
       "The committee's questions are probabilistic: how likely is sepsis given what we observe?")

# ── State spaces ─────────────────────────────────────────────────────
latris("bn", "set-state-space", "Age over 65", "yes,no")
latris("bn", "set-state-space", "Immunosuppression", "yes,no")
latris("bn", "set-state-space", "Suspected infection", "yes,no")
latris("bn", "set-state-space", "Sepsis", "yes,no")
latris("bn", "set-state-space", "Rising SOFA score", "yes,no")
latris("bn", "set-state-space", "Elevated lactate", "yes,no")

# ── CPTs, each with its provenance ───────────────────────────────────
# Priors for the ward population (illustrative of a general medical ward).
latris("bn", "set-cpt", "Age over 65", "--probs", "0.4,0.6", "--origin", "data-derived")
latris("bn", "set-cpt", "Immunosuppression", "--probs", "0.2,0.8", "--origin", "data-derived")

# Suspected infection | Age over 65, Immunosuppression
# rows (Age slowest): (65+,yes) (65+,no) (under65,yes) (under65,no)
latris("bn", "set-cpt", "Suspected infection",
       "--parents", "Age over 65,Immunosuppression",
       "--probs", "0.50,0.50,0.35,0.65,0.35,0.65,0.20,0.80",
       "--origin", "human-elicited", "--source", "seymour2016")

# Sepsis | Suspected infection, Immunosuppression
# Among suspected infections roughly one in six progresses (Sepsis-3 cohorts).
latris("bn", "set-cpt", "Sepsis",
       "--parents", "Suspected infection,Immunosuppression",
       "--probs", "0.30,0.70,0.15,0.85,0.02,0.98,0.005,0.995",
       "--origin", "human-elicited", "--source", "singer2016")

# Rising SOFA score | Sepsis — the Sepsis-3 marker of organ dysfunction.
latris("bn", "set-cpt", "Rising SOFA score", "--parents", "Sepsis",
       "--probs", "0.85,0.15,0.10,0.90",
       "--origin", "human-elicited", "--source", "seymour2016")

# Elevated lactate | Sepsis — hypoperfusion marker in the SSC guidelines.
latris("bn", "set-cpt", "Elevated lactate", "--parents", "Sepsis",
       "--probs", "0.55,0.45,0.06,0.94",
       "--origin", "human-elicited", "--source", "evans2021")

latris("bn", "check")

# ── Evidence checks (verbatim quotes from the stored extracts) ───────
latris("evidence", "check", "Suspected infection -> Sepsis", "description", "singer2016",
       "supports", "--rationale", "Sepsis-3 defines sepsis as organ dysfunction from a dysregulated response to infection.")
latris("evidence", "check", "Sepsis -> Rising SOFA score", "description", "seymour2016",
       "supports", "--rationale", "An increase of 2+ SOFA points identified organ dysfunction in suspected infection.")

# ── The showcase analyses (recorded for the report) ──────────────────
latris("bn", "marginals")
# Predictive: a patient with suspected infection.
latris("bn", "query", "--evidence", "Suspected infection=yes", "--query", "Sepsis")
# Diagnostic: SOFA rising and lactate high — what the screening pathway watches.
latris("bn", "query", "--evidence", "Rising SOFA score=yes", "--evidence", "Elevated lactate=yes",
       "--query", "Sepsis", "--query", "Suspected infection")
# The most likely explanation when sepsis is confirmed.
latris("bn", "explain", "--evidence", "Sepsis=yes")
# Which CPT parameters move the answer most.
latris("bn", "sensitivity", "Sepsis", "--state", "yes", "--top", "8")
# How sure is the key posterior when the tables are estimates?
latris("bn", "set-uncertainty", "Sepsis", "--n", "40",
       "--reason", "Progression rates elicited from the literature, not local data")
latris("bn", "set-uncertainty", "Rising SOFA score", "--n", "100",
       "--reason", "Sensitivity/specificity from the Sepsis-3 derivation cohort")
latris("bn", "monte-carlo", "Sepsis", "--state", "yes",
       "--evidence", "Rising SOFA score=yes", "--runs", "500")

latris("finding", "add",
       "A rising SOFA score and an elevated lactate together raise the probability of sepsis "
       "several-fold above the ward base rate.",
       "--category", "inference", "--target", "Sepsis",
       "--detail", "From the diagnostic query: conditioning on both observations moves P(Sepsis=yes) "
                   "far more than either alone.")
