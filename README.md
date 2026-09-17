# Compliance-as-Code Toolkit

[![Compliance Check](../../actions/workflows/compliance-check.yml/badge.svg)](../../actions/workflows/compliance-check.yml)

Working automation that treats compliance evidence and control mappings the way software treats code: version-controlled, validated on every change, and continuously checked for drift — rather than a spreadsheet that goes stale between audits.

Built and maintained by **Quibble Security LLC** as the automation layer behind the [grc-governance-framework](../grc-governance-framework) methodology. All data in `sample_data/` is fictional, used only to demonstrate the tooling.

## What this actually does

Three scripts, wired into a GitHub Actions pipeline that runs on every push, every PR, and weekly on a schedule (so staleness is caught even when nothing changes):

| Script | What it catches |
|---|---|
| [`validate_control_mapping.py`](scripts/validate_control_mapping.py) | Malformed control records, invalid statuses, duplicate control IDs, and **critical gaps** — high-risk controls that are Not Met/Not Started with no evidence linked |
| [`evidence_freshness_check.py`](scripts/evidence_freshness_check.py) | Evidence past a staleness threshold (warning) or a hard-fail threshold (CI failure) — the same "continuous monitoring" pattern platforms like Vanta/Drata run automatically |
| [`generate_compliance_report.py`](scripts/generate_compliance_report.py) | Nothing — it summarizes the above into a Markdown status report, broken out by framework, with coverage % and an open-gaps list |

This is the same logic used to sanity-check control matrices and evidence exports on real engagements, generalized and pointed at fictional sample data.

## Try it

```bash
pip install -r requirements.txt

# Validate the sample control mapping (exits non-zero on critical gaps)
python scripts/validate_control_mapping.py --input sample_data/controls.csv

# Check evidence freshness (exits non-zero past the hard-fail threshold)
python scripts/evidence_freshness_check.py --input sample_data/evidence.csv --stale-days 90 --hard-fail-days 180

# Generate a Markdown status report
python scripts/generate_compliance_report.py --controls sample_data/controls.csv --evidence sample_data/evidence.csv --output compliance-report.md

# Run the test suite
pytest tests/ -v
```

Running the validator against the included sample data on purpose surfaces two critical gaps and one stale/one hard-failed evidence item — that's the point: this is what the checks look like when they actually find something.

## CI pipeline

See [`.github/workflows/compliance-check.yml`](.github/workflows/compliance-check.yml). On every push/PR it runs the unit tests, both validators, and publishes the generated report as a build artifact. It also runs on a weekly schedule (`workflow_dispatch` too) so evidence aging past the freshness threshold gets caught even on a quiet repo — the same reason continuous-monitoring platforms poll on a schedule rather than only on evidence upload.

## Repository structure

```
compliance-as-code-toolkit/
├── scripts/
│   ├── validate_control_mapping.py
│   ├── evidence_freshness_check.py
│   └── generate_compliance_report.py
├── sample_data/
│   ├── controls.csv       # fictional control mapping
│   └── evidence.csv       # fictional evidence log
├── tests/                 # pytest unit tests for each script
├── .github/workflows/
│   └── compliance-check.yml
└── requirements.txt
```

## Using this on a real engagement

Point `--input`/`--controls`/`--evidence` at your own exports (e.g., a Vanta control export, or a manually maintained matrix) — the CSV schemas are documented in each script's docstring. The CI workflow can run against a private repo per client, or against a shared evidence export pulled from the GRC platform's API on a schedule.

## Related

- [grc-governance-framework](../grc-governance-framework) — the methodology and document templates these checks are built to support.

## License

[MIT License](LICENSE).
