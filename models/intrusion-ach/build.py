"""Build the Unusual activity on the network example model.

Applies spec.yaml (substrate, context, sources), then builds the ACH
matrix: three hypotheses, eight evidence items with credibility and
relevance, and twenty-four ratings with rationales where evidence counts
against a hypothesis. Records the showcase analysis: the ranking by
evidence-against, the linchpins, and the items that don't discriminate.

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
latris("project", "select-models", "ach")
latris("project", "choose", "ach", "--why",
       "The team must not anchor on the easy explanation; the matrix forces them to ask "
       "what the evidence rules out, not what confirms the favourite.")

EXFIL = "Malicious exfiltration"
BACKUP = "Misconfigured backup job"
VENDOR = "Compromised vendor credential"

TIMING = "Traffic began minutes after a scheduled backup change"
CLOUD = "Destination is a known cloud storage range"
NOLAT = "No lateral movement observed"
LEAK = "Vendor reported a credential leak last month"
VOLUME = "Volume matches the nightly backup size"
RECURS = "Traffic recurs nightly at the same time"
EDR = "EDR raised no process alerts"
FWCHANGE = "Firewall change request references the storage range"

# ── Hypotheses and evidence items ────────────────────────────────────
for hypothesis in (EXFIL, BACKUP, VENDOR):
    latris("ach", "element", hypothesis, "hypothesis")
for item in (TIMING, CLOUD, NOLAT, LEAK, VOLUME, RECURS, EDR, FWCHANGE):
    latris("ach", "element", item, "evidence_item")

# ── Item quality: how far each can be trusted, how directly it bears ─
latris("ach", "item", TIMING, "--credibility", "high", "--relevance", "high",
       "--notes", "From the change-management log; timestamps cross-checked with NetFlow.")
latris("ach", "item", CLOUD, "--credibility", "high", "--relevance", "medium",
       "--notes", "DNS and egress logs; 'known range' says little by itself.")
latris("ach", "item", NOLAT, "--credibility", "medium", "--relevance", "high",
       "--notes", "Absence evidence — depends on monitoring coverage.")
latris("ach", "item", LEAK, "--credibility", "medium", "--relevance", "medium",
       "--notes", "Vendor's own disclosure; scope of the leak unconfirmed.")
latris("ach", "item", VOLUME, "--credibility", "high", "--relevance", "high",
       "--notes", "Byte counts from the egress logs against backup history.")
latris("ach", "item", RECURS, "--credibility", "high", "--relevance", "high",
       "--notes", "Five consecutive nights, same window.")
latris("ach", "item", EDR, "--credibility", "medium", "--relevance", "medium",
       "--notes", "Absence evidence; EDR coverage on the VLAN is good but not total.")
latris("ach", "item", FWCHANGE, "--credibility", "high", "--relevance", "high",
       "--notes", "Documented change request naming the destination range.")

latris("assumption", "add", "Monitoring coverage is good enough that absent lateral movement means something.",
       "--rationale", "Otherwise the strongest item against exfiltration would carry no weight.",
       "--target", NOLAT)

# ── The matrix: rate every item against every hypothesis ─────────────
def rate(item, hypothesis, rating, rationale=None, verified=False):
    args = [item, hypothesis, rating]
    if rationale:
        args += ["--rationale", rationale]
    if verified:
        args.append("--verified")
    latris("ach", "rate", *args)

# Timing of the change window
rate(TIMING, EXFIL, "I", "An attacker already in place would not wait for a change window.", verified=True)
rate(TIMING, BACKUP, "CC")
rate(TIMING, VENDOR, "N")
# Destination range
rate(CLOUD, EXFIL, "C")
rate(CLOUD, BACKUP, "CC")
rate(CLOUD, VENDOR, "C")
# No lateral movement
rate(NOLAT, EXFIL, "I", "Exfiltration at this volume usually shows staging; none observed.", verified=True)
rate(NOLAT, BACKUP, "C")
rate(NOLAT, VENDOR, "N")
# The vendor's leaked credential
rate(LEAK, EXFIL, "N")
rate(LEAK, BACKUP, "N")
rate(LEAK, VENDOR, "CC")
# Volume match
rate(VOLUME, EXFIL, "N")
rate(VOLUME, BACKUP, "CC")
rate(VOLUME, VENDOR, "N")
# Nightly recurrence
rate(RECURS, EXFIL, "I", "A one-off theft would not recur on the backup schedule.", verified=True)
rate(RECURS, BACKUP, "CC")
rate(RECURS, VENDOR, "C")
# EDR silence
rate(EDR, EXFIL, "I", "Data staging of this size would trip the process monitors.", verified=True)
rate(EDR, BACKUP, "C")
rate(EDR, VENDOR, "C")
# The firewall change request
rate(FWCHANGE, EXFIL, "I", "An attacker would not file the paperwork that documents the destination.", verified=True)
rate(FWCHANGE, BACKUP, "CC")
rate(FWCHANGE, VENDOR, "N")

latris("ach", "check")

# ── Evidence: Heuer backs the disconfirmation method ─────────────────
latris("evidence", "add", EXFIL, "description", "heuer1999")
latris("evidence", "check", EXFIL, "description", "heuer1999",
       "supports", "--rationale", "The matrix is built Heuer's way: seek what refutes each "
                                  "hypothesis. Five items count against exfiltration.")

# ── The showcase analysis (recorded for the report) ──────────────────
latris("ach", "analyse")

latris("finding", "add",
       "The evidence rules against malicious exfiltration; two hypotheses survive — the "
       "misconfigured backup job and the compromised vendor credential.",
       "--category", "inference", "--target", EXFIL,
       "--detail", "Five items are inconsistent with exfiltration — timing, no lateral movement, "
                   "nightly recurrence, EDR silence and the documented firewall change. The backup "
                   "job fits all eight items; the vendor credential fits fewer, but ACH rules out, "
                   "it does not crown — and nothing contradicts it.")
latris("finding", "add",
       "The compromised vendor credential cannot yet be ruled out; it survives on neutral ratings.",
       "--category", "recommendations", "--target", VENDOR,
       "--detail", "Nothing in the matrix contradicts it. Before closing the incident, check "
                   "whether vendor access touched the finance VLAN — that one observation would "
                   "discriminate.")
