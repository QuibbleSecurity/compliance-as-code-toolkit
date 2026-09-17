#!/usr/bin/env python3
"""
validate_control_mapping.py

Validates a control mapping CSV (control_id, framework, control_family,
control_description, status, risk_rating, evidence_id) for structural
integrity and audit-readiness red flags:

  - required columns present
  - no blank control_id / framework / control_description
  - status is one of the allowed values
  - "Met" controls that have risk_rating populated (should be blank/None once remediated risk is closed)
  - non-"Met" controls with a High risk_rating and no linked evidence_id ("critical gap")
  - duplicate control_id within the same framework

Exit code 0 = no issues (or only warnings, unless --strict).
Exit code 1 = one or more errors found, or warnings found with --strict.

Usage:
    python validate_control_mapping.py --input sample_data/controls.csv
    python validate_control_mapping.py --input sample_data/controls.csv --strict
"""
import argparse
import csv
import sys
from collections import defaultdict

REQUIRED_COLUMNS = {
    "control_id", "framework", "control_family",
    "control_description", "status", "risk_rating", "evidence_id",
}
ALLOWED_STATUSES = {"Met", "Partially Met", "Not Met", "Not Applicable", "Not Started"}
ALLOWED_RISK_RATINGS = {"", "Low", "Medium", "High"}


def load_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required column(s): {', '.join(sorted(missing))}")
        return list(reader)


def validate(rows):
    errors = []
    warnings = []
    seen = defaultdict(int)

    for i, row in enumerate(rows, start=2):  # +2: header row + 1-indexing
        control_id = row["control_id"].strip()
        framework = row["framework"].strip()
        description = row["control_description"].strip()
        status = row["status"].strip()
        risk = row["risk_rating"].strip()
        evidence = row["evidence_id"].strip()

        if not control_id:
            errors.append(f"Row {i}: missing control_id")
            continue
        if not framework:
            errors.append(f"Row {i} ({control_id}): missing framework")
        if not description:
            errors.append(f"Row {i} ({control_id}): missing control_description")
        if status not in ALLOWED_STATUSES:
            errors.append(f"Row {i} ({control_id}): invalid status '{status}'")
        if risk not in ALLOWED_RISK_RATINGS:
            errors.append(f"Row {i} ({control_id}): invalid risk_rating '{risk}'")

        if status == "Met" and not evidence:
            warnings.append(f"Row {i} ({control_id}): status is 'Met' but no evidence_id is linked")

        if status in ("Not Met", "Partially Met", "Not Started") and risk == "High" and not evidence:
            errors.append(
                f"Row {i} ({control_id}): CRITICAL GAP — status '{status}', risk 'High', no evidence linked"
            )

        seen[(framework, control_id)] += 1

    for (framework, control_id), count in seen.items():
        if count > 1:
            errors.append(f"Duplicate control_id '{control_id}' in framework '{framework}' ({count} occurrences)")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Validate a control mapping CSV.")
    parser.add_argument("--input", required=True, help="Path to control mapping CSV")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    try:
        rows = load_rows(args.input)
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    errors, warnings = validate(rows)

    print(f"Validated {len(rows)} control(s) from {args.input}")
    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  ✗ {e}")
    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  ! {w}")
    if not errors and not warnings:
        print("No issues found.")

    if errors or (args.strict and warnings):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
