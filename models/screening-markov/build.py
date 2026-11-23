"""Build the Is the screening programme worth its cost? example model.

Applies spec.yaml (substrate, context, sources), then parameterises the
Markov cohort: four health states, two strategies, annual cycles over
thirty years with NICE-style discounting. Records the showcase analysis:
the incremental cost-effectiveness of screening against no screening at
the committee's willingness-to-pay threshold.

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
latris("project", "select-models", "markov")
latris("project", "choose", "markov", "--why",
       "A cohort moving between health states over years, compared under two strategies on cost and QALYs.")

# ── States and strategies ────────────────────────────────────────────
for state in ("Healthy", "Undetected cancer", "Detected cancer", "Dead"):
    latris("markov", "element", state, "state")
latris("markov", "element", "Screening programme", "strategy")
latris("markov", "element", "No screening", "strategy")

# ── Run settings: 30 annual cycles, NICE-style 3.5% discounting ─────
latris("markov", "settings", "--cycles", "30", "--cycle-length", "1",
       "--time-units", "years", "--discount", "0.035", "--half-cycle",
       "--wtp", "20000", "--cost-units", "£", "--outcome-units", "QALY")

# ── Start: everyone healthy ──────────────────────────────────────────
latris("markov", "start", "Healthy", "1.0")

# ── Transition probabilities (per year), with provenance ─────────────
# Incidence in the 50–74 cohort.
latris("markov", "transition", "Healthy -> Undetected cancer", "0.002",
       "--origin", "data-derived",
       "--notes", "Illustrative annual incidence for the screening-age cohort.")
# Diagnosis: screening finds cancers before symptoms would.
latris("markov", "transition", "Undetected cancer -> Detected cancer", "0.25",
       "--strategy", "No screening", "--origin", "human-elicited",
       "--notes", "Symptom-led diagnosis in the unscreened cohort.")
latris("markov", "transition", "Undetected cancer -> Detected cancer", "0.50",
       "--strategy", "Screening programme", "--origin", "human-elicited",
       "--notes", "Regular screening roughly doubles the annual detection rate.")
# Late-stage mortality while undetected (same under both strategies).
latris("markov", "transition", "Undetected cancer -> Dead", "0.08",
       "--origin", "human-elicited",
       "--notes", "Late-stage disease carries the worst survival.")
# Mortality after detection — screening shifts diagnosis earlier, and the
# Minnesota trial measured the mortality benefit of earlier detection.
latris("markov", "transition", "Detected cancer -> Dead", "0.05",
       "--strategy", "No screening", "--source", "mandel1993",
       "--origin", "human-elicited", "--verified",
       "--notes", "Baseline annual mortality after symptomatic diagnosis.")
latris("markov", "transition", "Detected cancer -> Dead", "0.0335",
       "--strategy", "Screening programme", "--source", "mandel1993",
       "--origin", "human-elicited", "--verified",
       "--notes", "Baseline x (1 - 0.33): the trial's 33% mortality reduction from annual screening.")

# ── Rewards: utility per year and cost per cycle ─────────────────────
latris("markov", "reward", "Healthy", "--utility", "1.0")
latris("markov", "reward", "Undetected cancer", "--utility", "0.85",
       "--origin", "human-elicited",
       "--notes", "Pre-diagnosis disutility, illustrative of published screening evaluations.")
latris("markov", "reward", "Detected cancer", "--utility", "0.70",
       "--origin", "human-elicited",
       "--notes", "On-treatment utility weight.")
latris("markov", "reward", "Dead", "--utility", "0.0", "--cost", "0")
# Costs: the programme itself, then treatment — cheaper when caught early.
latris("markov", "reward", "Healthy", "--cost", "30",
       "--strategy", "Screening programme", "--origin", "human-elicited",
       "--notes", "Kit, administration and follow-up per person-year, illustrative.")
latris("markov", "reward", "Detected cancer", "--cost", "8000",
       "--strategy", "No screening", "--origin", "human-elicited",
       "--notes", "Late-stage treatment cost per year, illustrative.")
latris("markov", "reward", "Detected cancer", "--cost", "5000",
       "--strategy", "Screening programme", "--origin", "human-elicited",
       "--notes", "Earlier-stage treatment is cheaper per year.")

latris("assumption", "add", "Background (non-cancer) mortality is ignored.",
       "--rationale", "The committee's question is about the incremental effect of screening; "
                      "all-cause mortality would move both strategies together.",
       "--target", "Dead")

latris("markov", "check")

# ── Evidence check (verbatim support from the stored extract) ────────
latris("evidence", "check", "Detected cancer -> Dead", "description", "mandel1993",
       "supports", "--rationale", "The Minnesota trial's 33% mortality reduction is why the screening "
                                  "strategy's post-detection mortality is set to two-thirds of baseline.")

# ── The showcase analysis (recorded for the report) ──────────────────
latris("markov", "analyse")

latris("finding", "add",
       "At £20,000 per QALY the screening programme is the strategy to choose.",
       "--category", "inference", "--target", "Screening programme",
       "--detail", "The incremental analysis puts the programme's ICER under the committee's "
                   "willingness-to-pay threshold over the thirty-year horizon.")
latris("finding", "add",
       "The case for screening rests on the survival benefit of earlier detection, "
       "not on treatment savings.",
       "--category", "dynamics", "--target", "Detected cancer -> Dead",
       "--detail", "The QALY gain comes from the lower post-detection mortality the trial measured; "
                   "cheaper earlier-stage treatment only softens the programme's cost.")
