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

# Validate the sample control mapping
python scripts/validate_control_mapping.py --input sample_data/controls.csv

# Check evidence freshness
python scripts/evidence_freshness_check.py --input sample_data/evidence.csv --stale-days 90 --hard-fail-days 180

# Generate a Markdown status report
python scripts/generate_compliance_report.py --controls sample_data/controls.csv --evidence sample_data/evidence.csv --output compliance-report.md

# Run the test suite
pytest tests/ -v
```

The `sample_data/` used above is a clean baseline (all controls Met, all evidence current) so the pipeline badge above reflects a healthy repo rather than a demo permanently stuck in a failing state.

## What it catches

The whole point of these checks is that they fail loudly when something's actually wrong. [`sample_data/example-with-gaps/`](sample_data/example-with-gaps/) is a second, deliberately broken dataset — same schema, same commands — that shows what that looks like:

```
$ python scripts/validate_control_mapping.py --input sample_data/example-with-gaps/controls.csv
Validated 8 control(s) from sample_data/example-with-gaps/controls.csv

2 error(s):
  ✗ Row 5 (CC7.2): CRITICAL GAP — status 'Not Met', risk 'High', no evidence linked
  ✗ Row 6 (CC9.2): CRITICAL GAP — status 'Not Started', risk 'High', no evidence linked

$ python scripts/evidence_freshness_check.py --input sample_data/example-with-gaps/evidence.csv --stale-days 90 --hard-fail-days 180
Checked 5 evidence item(s) from sample_data/example-with-gaps/evidence.csv

1 stale item(s) (warning):
  ! EV-003 (CC6.6, owner: IT Manager): 125 days old (stale threshold: 90)

1 critical item(s) (error):
  ✗ EV-005 (PR.AT-1, owner: HR): 200 days old (hard-fail threshold: 180)
```

Both commands exit non-zero here, which is what fails a real CI run — this is what a client's repo looks like the week before an audit if a control slips or evidence goes stale.

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
│   ├── controls.csv               # fictional control mapping (clean baseline)
│   ├── evidence.csv               # fictional evidence log (clean baseline)
│   └── example-with-gaps/         # same schema, deliberately broken — see "What it catches"
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
