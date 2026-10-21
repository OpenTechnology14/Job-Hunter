---
name: audits
description: Job-Hunter's audit pattern (evidence-backed verdicts, gap IDs, audit matrix, route ledger, pressure tests) and lightweight PR triage against the PR template and safety boundaries.
when_to_use: Use when asked to audit the repo or a subsystem, assess release readiness, update GAP_AUDIT/AUDIT docs, review or triage a PR, or check whether a change regresses safety/privacy. Triggers - "audit", "readiness", "gap", "is this release-ready", "review this PR", "triage PRs", "security review".
---

# Audits — Job-Hunter

Sources: `docs/AUDIT.md`, `docs/GAP_AUDIT.md`,
`docs/FULL_APPLICATION_AUDIT_MATRIX.md`, `docs/API_ROUTE_AUDIT_LEDGER.md`,
`docs/PRESSURE_TEST_LOAD.md`, `docs/OPEN_SOURCE_RELEASE_CHECKLIST.md`,
`docs/CONTINUOUS_IMPROVEMENT.md`, `.github/PULL_REQUEST_TEMPLATE.md`.

## Audit pattern (as established 2026-07-12)

1. **Scope line + date** at the top.
2. **Executive verdict per release profile** — local single-user vs hosted
   multi-user, never blended (e.g. "conditional GO local / NO-GO hosted").
3. **Executed-evidence table:** Check | Result (Pass / Partial / Fail) | Notes.
   Only things you ran. Skipped live checks are listed as skipped, with why.
4. **Gates** split P0-local and P0-hosted.
5. **Scope limitations** — what wasn't tested (live providers, real
   submission, public deployment, full-history secret scan).

Companion ledgers to update in the same pass:

| Doc | Update when |
|---|---|
| `GAP_AUDIT.md` | New gap → next `JH-0NN` ID, priority (P0 local / P0 hosted / P1 / P2), direct injection location, acceptance evidence. Closed gap → mark with the evidence, don't silently delete. |
| `FULL_APPLICATION_AUDIT_MATRIX.md` | A surface's status/evidence changes |
| `API_ROUTE_AUDIT_LEDGER.md` | Any route added/removed in `admin/server.py` |
| `PRESSURE_TEST_LOAD.md` | New failure mode; record command, commit, seed, env, elapsed, memory, errors, recovery |
| `OPEN_SOURCE_RELEASE_CHECKLIST.md` | A checklist item is proven |

Every escaped defect → regression test + (if systemic) a gap entry.
Live-provider results are smoke evidence, not deterministic release evidence.

## Standard audit checks

Python syntax across all `.py`; `python run_tests.py` by category; tracked-file
secret/PII scan (`.env`, `credentials/`, `output/`, `profiles/*.py` must be
ignored); CI presence; test isolation (no active-profile import/print/output);
doc consistency (counts, commands); admin routes for auth/CSRF; dry-run
non-submission.

## PR triage

**Thin convention — stated honestly:** the repo has a PR template but **no CI
workflow** (`.github/workflows/` absent, gap JH-001), no branch protection on
`main`, no CODEOWNERS, no labels convention, and very few PRs to date.
"CI green" currently means *no checks configured*; say that explicitly rather
than reporting green.

Minimum triage per PR:

1. Template checklist present and truthful (`run_tests.py` passes; no secrets/PII;
   source ToS + rate limits respected; docs updated; `CONTRIBUTING.md` conventions).
2. **Diff PII scan** — real names, emails, phones, cities, resumes, `.env` values.
   `main` was history-rewritten once to scrub these; don't reintroduce them.
3. **Safety boundary** — any change to `browser_apply.py`, `run_apply.py`, or
   submit paths: confirm dry-run still can't submit and confirmation is per-job.
4. **Privacy boundary** — any outbound payload (OpenTech, Sheets, webhooks)
   is an allow-list with no resumes/answers/credentials/paths.
5. **Hosted claims** — reject wording that implies `--deployed` is production-safe.
6. **Locked decisions** (see `design` skill) — if touched, require a proposal.
7. Classify: merge / request changes / needs proposal. Docs-only PRs still get
   steps 2 and 5.
