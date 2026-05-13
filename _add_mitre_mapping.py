"""
Add MITRE ATT&CK / OWASP / ENISA mapping columns to classification.csv.

Maps each of the 8 axis-B vectors + the 4 axis-F prompt-injection types
to canonical categories. Designed to kill the reviewer attack "why these
vectors and not the threat-intel community's existing taxonomy?".

New columns added (right of `notes`):
  mitre_attack      - primary MITRE ATT&CK technique ID + name
  owasp             - primary OWASP risk (Top 10 web or LLM Top 10)
  enisa             - primary ENISA Threat Landscape category
  mitre_pi          - extra MITRE technique for the prompt-injection axis,
                       only filled when prompt_injection != none/empty
"""
from __future__ import annotations

import csv
from pathlib import Path

PATH = Path("classification.csv")

# Axis B (vector_primary) -> MITRE / OWASP / ENISA
VECTOR_MAP = {
    "phishing_clone": (
        "T1566.002 Spearphishing Link",
        "A07:2021 Identification and Authentication Failures",
        "Phishing",
    ),
    "credential_harvest": (
        "T1056.003 Web Portal Capture",
        "A07:2021 Identification and Authentication Failures",
        "Phishing",
    ),
    "dark_patterns": (
        "T1204.001 User Execution: Malicious Link",
        "A04:2021 Insecure Design",
        "Social Engineering",
    ),
    "reward_trap": (
        "T1566 Phishing (incentive-based lure)",
        "A04:2021 Insecure Design",
        "Social Engineering",
    ),
    "authority_impersonation": (
        "T1656 Impersonation",
        "A07:2021 Identification and Authentication Failures",
        "Impersonation",
    ),
    "conversational_deception": (
        "T1656 Impersonation (interactive)",
        "OWASP LLM02 Insecure Output Handling",
        "Social Engineering",
    ),
    "fake_trust_signals": (
        "T1036.005 Masquerading: Match Legitimate Name/Location",
        "A07:2021 Identification and Authentication Failures",
        "Impersonation",
    ),
    "prompt_injection": (
        # Rare: prompt_injection as the primary vector. Falls through to PI
        # axis below in most rows.
        "T1059 Command and Scripting Interpreter",
        "OWASP LLM01 Prompt Injection",
        "Adversarial AI / Prompt manipulation",
    ),
    "none": ("n/a (benign baseline)", "n/a", "n/a"),
    "": ("", "", ""),
}

# Axis F (prompt_injection) extra MITRE map
PI_MAP = {
    "none": "",
    "":     "",
    "visible_text":    "T1059 + OWASP LLM01 (visible page text injects instruction)",
    "hidden_dom":      "T1564 Hide Artifacts + OWASP LLM01 (hidden DOM)",
    "fake_system_msg": "T1656 + OWASP LLM01 (forged system-role message)",
}


def main() -> None:
    with PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    new_cols = ["mitre_attack", "owasp", "enisa", "mitre_pi"]
    for c in new_cols:
        if c not in fieldnames:
            fieldnames.append(c)

    unknown_vectors: set[str] = set()
    unknown_pi: set[str] = set()
    for row in rows:
        vec = (row.get("vector_primary") or "").strip().lower()
        mitre, owasp, enisa = VECTOR_MAP.get(vec, ("UNMAPPED", "UNMAPPED", "UNMAPPED"))
        if vec and vec not in VECTOR_MAP:
            unknown_vectors.add(vec)
        row["mitre_attack"] = mitre
        row["owasp"] = owasp
        row["enisa"] = enisa
        pi = (row.get("prompt_injection") or "").strip().lower()
        pi_extra = PI_MAP.get(pi, "")
        if pi and pi not in PI_MAP:
            unknown_pi.add(pi)
        row["mitre_pi"] = pi_extra

    with PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {len(rows)} rows in {PATH}")
    print(f"New columns: {new_cols}")
    if unknown_vectors:
        print(f"WARNING: unmapped vector_primary values: {sorted(unknown_vectors)}")
    if unknown_pi:
        print(f"WARNING: unmapped prompt_injection values: {sorted(unknown_pi)}")


if __name__ == "__main__":
    main()
