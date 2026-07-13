# Continuous Improvement

## Cadence

- **Every change:** offline unit/contract tests, formatting/lint, secret scan, documentation link check.
- **Weekly:** provider smoke tests, failed-source review, flaky-test and selector-drift review.
- **Monthly:** synthetic clean setup, backup/restore, dependency/license review, submission-safety regression suite.
- **Before release:** clean clone, supported-Python matrix, tracked/history secret scan, open-source checklist, known limitations.
- **Before enabling hosted mode:** threat model, route authorization matrix, tenant-isolation pressure test, upload and CSRF review.

## Metrics

Track deterministic suite pass rate, live-source availability separately, duplicate rate, scrape duration, parse rejection rate, browser safe-stop rate, submission-confirmation violations (target zero), CSV recovery failures (zero), and documentation drift.

Every escaped defect should produce a regression fixture/test and, when systemic, a gap-ledger entry. Provider downtime does not justify weakening deterministic release gates.
