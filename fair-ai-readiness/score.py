#!/usr/bin/env python3
"""
fair-scientific-data v0.1 — FAIR AI-Readiness Scorer

Usage:
    python fair-ai-readiness/score.py <assessment.yaml>

The assessment YAML is a copy of rubric.yaml with each criterion's `status`
field filled in as YES, PARTIAL, or NO.

Outputs:
    - Per-dimension scores
    - Overall score (0–100%)
    - Readiness tier: Not Ready | Developing | Ready | AI-Ready
    - Criteria that scored NO or PARTIAL (action items)

Sources:
    FAIRSCAPE 28 AI-readiness criteria:
        Al Manir et al. bioRxiv:2024.12.23.629818 v4 (2026). PMC:11703166.
    Bridge2AI 7 metadata dimensions:
        Caufield et al. arXiv:2509.10432 (2025).
"""

import sys
import pathlib
import argparse

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

SCORE_MAP = {
    # Strings (quoted in YAML)
    "YES": 1.0,
    "yes": 1.0,
    "Y": 1.0,
    "PARTIAL": 0.5,
    "partial": 0.5,
    "P": 0.5,
    "NO": 0.0,
    "no": 0.0,
    "N": 0.0,
    # YAML booleans (YES/NO unquoted parsed as True/False by PyYAML)
    True: 1.0,
    False: 0.0,
    None: None,  # Not answered — excluded from denominator
}

TIERS = [
    (0.90, "AI-Ready",   "Dataset meets the bar for biomedical AI training/evaluation."),
    (0.70, "Ready",      "Dataset is FAIR and well-documented; minor gaps remain."),
    (0.40, "Developing", "Core FAIR properties present; significant AI-readiness gaps."),
    (0.00, "Not Ready",  "Substantial FAIR and AI-readiness work required."),
]


def score_criteria(criteria: list) -> tuple[float, float, int, int, list]:
    """Returns (earned, max_possible, answered, total, action_items)."""
    earned = 0.0
    max_possible = 0.0
    answered = 0
    total = len(criteria)
    action_items = []

    for c in criteria:
        status = c.get("status")
        score = SCORE_MAP.get(status)
        if score is None and status is not None:
            # Try resolving string representations of booleans that YAML may produce
            str_status = str(status).upper()
            if str_status in ("TRUE", "YES", "Y"):
                score = 1.0
            elif str_status in ("FALSE", "NO", "N"):
                score = 0.0
            else:
                print(f"  WARNING: Unknown status '{status}' for {c.get('id', '?')} — treated as unanswered.")
                score = None

        if score is not None:
            answered += 1
            earned += score
            max_possible += 1.0
            if score < 1.0:
                action_items.append({
                    "id": c.get("id"),
                    "label": c.get("label"),
                    "status": status,
                    "notes": c.get("notes", ""),
                    "source": c.get("source", ""),
                })

    return earned, max_possible, answered, total, action_items


def tier_for_score(fraction: float) -> tuple[str, str]:
    for threshold, name, description in TIERS:
        if fraction >= threshold:
            return name, description
    return "Not Ready", TIERS[-1][2]


def main():
    parser = argparse.ArgumentParser(description="Score a FAIR AI-readiness self-assessment YAML.")
    parser.add_argument("assessment", help="Path to filled-in assessment YAML (copy of rubric.yaml)")
    parser.add_argument("--output", "-o", default=None, help="Write report to file instead of stdout")
    args = parser.parse_args()

    path = pathlib.Path(args.assessment)
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(2)

    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)

    lines = [
        "# FAIR AI-Readiness Score Report",
        f"",
        f"**Assessment file**: `{path}`",
        f"",
        "## Dimension Scores",
        "",
        "| Dimension | Earned | Max | Score | Unanswered |",
        "|-----------|--------|-----|-------|-----------|",
    ]

    total_earned = 0.0
    total_max = 0.0
    all_action_items = []

    for key, value in doc.items():
        if not key.startswith("dimension_") or not isinstance(value, dict):
            continue
        criteria = value.get("criteria", [])
        if not criteria:
            continue

        earned, max_p, answered, total, action_items = score_criteria(criteria)
        total_earned += earned
        total_max += max_p
        all_action_items.extend(action_items)
        unanswered = total - answered
        pct = f"{earned / max_p * 100:.0f}%" if max_p > 0 else "—"
        lines.append(f"| {value.get('label', key)} | {earned:.1f} | {max_p:.0f} | {pct} | {unanswered} |")

    lines += [""]

    overall = total_earned / total_max if total_max > 0 else 0.0
    tier_name, tier_desc = tier_for_score(overall)

    lines += [
        f"## Overall Score",
        f"",
        f"**{total_earned:.1f} / {total_max:.0f} = {overall * 100:.1f}%**",
        f"",
        f"**Readiness Tier: {tier_name}**",
        f"> {tier_desc}",
        f"",
        "| Tier | Range |",
        "|------|-------|",
        "| AI-Ready | ≥ 90% |",
        "| Ready | 70–89% |",
        "| Developing | 40–69% |",
        "| Not Ready | < 40% |",
        "",
    ]

    if all_action_items:
        lines += [
            "## Action Items (Criteria scoring < YES)",
            "",
            "| ID | Label | Status | Source |",
            "|----|-------|--------|--------|",
        ]
        for item in all_action_items:
            note = f" _{item['notes']}_" if item.get("notes") else ""
            display_status = item['status']
            if display_status is True:
                display_status = "YES"
            elif display_status is False:
                display_status = "NO"
            elif display_status is None:
                display_status = "unanswered"
            lines.append(f"| {item['id']} | {item['label']}{note} | {display_status} | {item['source']} |")
    else:
        lines.append("## Action Items\n\nAll criteria scored YES. Well done!")

    report = "\n".join(lines)

    if args.output:
        pathlib.Path(args.output).write_text(report, encoding="utf-8")
        print(f"Report written to: {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
