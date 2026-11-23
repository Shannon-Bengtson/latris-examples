"""Build the Does mentoring raise school completion? example model.

Applies spec.yaml (substrate, context, sources), lays the five-link results
chain out by level, sets a prior on every link with its provenance, and
runs process-tracing tests — three passed, two designed but not yet run.
Then traces the posteriors and estimates the impact on attendance from
register data (difference-in-differences against a comparison group).

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
latris("project", "select-models", "theory_of_change")
latris("project", "choose", "theory_of_change", "--why",
       "Renewal turns on whether the causal story holds link by link, and the board wants "
       "to see which links are proven and which are not.")

# ── Levels in the results chain ──────────────────────────────────────
latris("toc", "level", "Mentor training", "activity")
latris("toc", "level", "Weekly mentoring sessions", "activity")
latris("toc", "level", "Students mentored", "output")
latris("toc", "level", "School attendance", "short_term_outcome")
latris("toc", "level", "Grades", "long_term_outcome")
latris("toc", "level", "School completion", "impact")

# ── Priors on every link, with provenance ────────────────────────────
latris("toc", "prior", "Mentor training -> Weekly mentoring sessions", "0.85",
       "--source", "dubois2011", "--origin", "human-elicited", "--verified",
       "--notes", "Programme design requires weekly sessions; the meta-analysis finds training "
                  "among the practices behind stronger effects.")
latris("toc", "prior", "Weekly mentoring sessions -> Students mentored", "0.9",
       "--origin", "human-direct", "--verified",
       "--notes", "Delivery is tracked; reaching students is not the risky part.")
latris("toc", "prior", "Students mentored -> School attendance", "0.6",
       "--source", "dubois2011", "--origin", "human-elicited",
       "--notes", "Small average effects across 73 evaluations ground a modest prior; "
                  "attendance is the most proximal outcome.")
latris("toc", "prior", "School attendance -> Grades", "0.7",
       "--origin", "human-elicited",
       "--notes", "Attendance is a precondition for learning, but not sufficient.")
latris("toc", "prior", "Grades -> School completion", "0.75",
       "--origin", "human-elicited",
       "--notes", "The link the board calls unproven.")

# ── Process-tracing tests ────────────────────────────────────────────
# Passed: hoop test on delivery (fails the link if the logs were absent).
latris("toc", "test", "Mentor training -> Weekly mentoring sessions", "Session logs",
       "--if-true", "0.95", "--if-false", "0.3", "--found",
       "--description", "Weekly session logs signed by trained mentors.",
       "--notes", "Logs on file for nine of ten mentors, covering the full year.",
       "--verified")
# Passed: doubly decisive on reach.
latris("toc", "test", "Weekly mentoring sessions -> Students mentored", "Mentoring registers",
       "--if-true", "0.95", "--if-false", "0.1", "--found",
       "--description", "Registers showing students with ten or more sessions.",
       "--notes", "212 students met the threshold this year.",
       "--verified")
# Passed: straw in the wind on the attendance link — the register data
# carries the weight here (see toc impact below).
latris("toc", "test", "Students mentored -> School attendance", "Attendance comparison",
       "--if-true", "0.7", "--if-false", "0.4", "--found",
       "--description", "Mentored students' attendance rising against matched non-mentored students.",
       "--notes", "Direction confirmed; size estimated separately from the register data.")
# Designed, not yet run: the two links the renewal case rests on.
latris("toc", "test", "School attendance -> Grades", "Grade records",
       "--if-true", "0.6", "--if-false", "0.4",
       "--description", "Attainment records for mentored students against their baseline year.")
latris("toc", "test", "Grades -> School completion", "Cohort tracking",
       "--if-true", "0.5", "--if-false", "0.2",
       "--description", "Three-year completion tracking of the first mentored cohort against "
                        "earlier cohorts.",
       "--notes", "The cohort is not old enough yet; this is the test to fund next.")

latris("toc", "check")

# ── Evidence check (verbatim support from the stored extract) ────────
latris("evidence", "check", "Students mentored -> School attendance", "description", "dubois2011",
       "supports", "--rationale", "The meta-analysis finds a small but significant average benefit, "
                                  "stronger with mentor training — grounds the modest prior, "
                                  "not a heroic one.")

# ── Trace: posteriors per link, pathway confidence, tests to run ─────
latris("toc", "trace")

# ── Impact on attendance from register data (DiD vs comparison) ──────
latris("data", "add", str(HERE / "attendance.csv"), "--name", "attendance",
       "--description", "Termly mean attendance (%) from school registers, programme vs "
                        "comparison schools. Synthetic illustration for the gallery.")
latris("toc", "impact", "School attendance", "--dataset", "attendance",
       "--time", "term", "--at", "6", "--group", "group", "--treated", "programme")

latris("assumption", "add", "Attendance is recorded the same way in both groups' registers.",
       "--rationale", "The difference-in-differences estimate is only as good as the comparison; "
                      "recording practice was confirmed with the schools.",
       "--target", "School attendance")

latris("finding", "add",
       "The front of the chain is solid; the case weakens after attendance.",
       "--category", "dynamics", "--target", "School completion",
       "--detail", "Delivery and reach passed strong tests and the attendance link has both a "
                   "passed test and a data estimate behind it. The links into grades and "
                   "completion rest on priors alone.")
latris("finding", "add",
       "The register data shows attendance stepping up when the programme began, against a "
       "flat comparison group.",
       "--category", "inference", "--target", "School attendance",
       "--detail", "The difference-in-differences estimate puts the gain at several percentage "
                   "points of termly attendance, with the pre-period parallel-trend check passed.")
latris("finding", "add",
       "Fund the cohort-tracking test before the next renewal round: it is the test that could "
       "move the weakest link most.",
       "--category", "recommendations", "--target", "Grades -> School completion",
       "--detail", "Trace ranks the unrun tests by how far they could move their link; completion "
                   "tracking sits at the top of that list.")
