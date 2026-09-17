#!/usr/bin/env python3
"""
evidence_freshness_check.py

Flags compliance evidence that has gone stale — mirrors the "continuous
monitoring" check a platform like Vanta or Drata runs automatically, so a
control isn't silently marked "Met" on evidence that's a year old.

Input CSV columns: evidence_id, control_id, description, last_updated (YYYY-MM-DD), owner

Usage:
    python evidence_freshness_check.py --input sample_data/evidence.csv --stale-days 90
    python evidence_freshness_check.py --input sample_data/evidence.csv --stale-days 90 --hard-fail-days 180
"""
import argparse
import csv
import sys
from datetime import date, datetime


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"evidence_id", "control_id", "description", "last_updated", "owner"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required column(s): {', '.join(sorted(missing))}")
        return list(reader)


def check(rows, stale_days, hard_fail_days, today=None):
    today = today or date.today()
    stale = []
    critical = []

    for row in rows:
        try:
            last_updated = datetime.strptime(row["last_updated"].strip(), "%Y-%m-%d").date()
        except ValueError:
            critical.append((row, None, f"unparseable last_updated '{row['last_updated']}'"))
            continue

        age_days = (today - last_updated).days
        if age_days > hard_fail_days:
            critical.append((row, age_days, f"{age_days} days old (hard-fail threshold: {hard_fail_days})"))
        elif age_days > stale_days:
            stale.append((row, age_days, f"{age_days} days old (stale threshold: {stale_days})"))

    return stale, critical


def main():
    parser = argparse.ArgumentParser(description="Check evidence freshness against a staleness threshold.")
    parser.add_argument("--input", required=True, help="Path to evidence CSV")
    parser.add_argument("--stale-days", type=int, default=90, help="Days before evidence is flagged stale (warning)")
    parser.add_argument("--hard-fail-days", type=int, default=180, help="Days before evidence fails CI (error)")
    args = parser.parse_args()

    try:
        rows = load_rows(args.input)
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    stale, critical = check(rows, args.stale_days, args.hard_fail_days)

    print(f"Checked {len(rows)} evidence item(s) from {args.input}")
    if stale:
        print(f"\n{len(stale)} stale item(s) (warning):")
        for row, age, msg in stale:
            print(f"  ! {row['evidence_id']} ({row['control_id']}, owner: {row['owner']}): {msg}")
    if critical:
        print(f"\n{len(critical)} critical item(s) (error):")
        for row, age, msg in critical:
            print(f"  ✗ {row['evidence_id']} ({row['control_id']}, owner: {row['owner']}): {msg}")
    if not stale and not critical:
        print("All evidence is current.")

    sys.exit(1 if critical else 0)


if __name__ == "__main__":
    main()
