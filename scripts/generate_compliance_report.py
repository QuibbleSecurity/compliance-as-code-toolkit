#!/usr/bin/env python3
"""
generate_compliance_report.py

Combines a control mapping CSV and an evidence CSV into a single Markdown
compliance status report: coverage by framework, open gaps, and stale
evidence. Intended to run in CI on a schedule (or on every push) so there's
always an up-to-date, reviewable snapshot of audit readiness.

Usage:
    python generate_compliance_report.py \
        --controls sample_data/controls.csv \
        --evidence sample_data/evidence.csv \
        --output report.md
"""
import argparse
import csv
from collections import defaultdict
from datetime import date, datetime


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_report(controls, evidence, stale_days=90, today=None):
    today = today or date.today()
    evidence_by_id = {e["evidence_id"]: e for e in evidence}

    by_framework = defaultdict(list)
    for c in controls:
        by_framework[c["framework"]].append(c)

    lines = [f"# Compliance Status Report", "", f"_Generated {today.isoformat()}_", ""]

    total_met = sum(1 for c in controls if c["status"] == "Met")
    lines.append(f"**Overall:** {total_met}/{len(controls)} controls Met "
                 f"({round(100 * total_met / len(controls))}% coverage)" if controls else "No controls found.")
    lines.append("")

    for framework, ctrls in sorted(by_framework.items()):
        met = sum(1 for c in ctrls if c["status"] == "Met")
        lines.append(f"## {framework} — {met}/{len(ctrls)} Met")
        lines.append("")
        lines.append("| Control | Status | Risk | Evidence | Evidence Age |")
        lines.append("|---|---|---|---|---|")
        for c in ctrls:
            ev_id = c.get("evidence_id", "").strip()
            ev_age = "—"
            if ev_id and ev_id in evidence_by_id:
                try:
                    last_updated = datetime.strptime(evidence_by_id[ev_id]["last_updated"], "%Y-%m-%d").date()
                    age_days = (today - last_updated).days
                    flag = " ⚠️" if age_days > stale_days else ""
                    ev_age = f"{age_days}d{flag}"
                except ValueError:
                    ev_age = "unparseable"
            elif ev_id:
                ev_age = "missing evidence record"
            lines.append(
                f"| {c['control_id']} | {c['status']} | {c.get('risk_rating') or '—'} "
                f"| {ev_id or '—'} | {ev_age} |"
            )
        lines.append("")

    gaps = [c for c in controls if c["status"] in ("Not Met", "Partially Met", "Not Started")]
    if gaps:
        lines.append("## Open Gaps")
        lines.append("")
        for c in sorted(gaps, key=lambda c: {"High": 0, "Medium": 1, "Low": 2, "": 3}.get(c.get("risk_rating", ""), 3)):
            lines.append(f"- **{c['control_id']}** ({c['framework']}, risk: {c.get('risk_rating') or 'unrated'}): "
                         f"{c['control_description']} — _{c['status']}_")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate a Markdown compliance status report.")
    parser.add_argument("--controls", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--output", default=None, help="Write to file instead of stdout")
    parser.add_argument("--stale-days", type=int, default=90)
    args = parser.parse_args()

    controls = load_csv(args.controls)
    evidence = load_csv(args.evidence)
    report = build_report(controls, evidence, stale_days=args.stale_days)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
