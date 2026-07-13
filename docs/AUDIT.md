# Job-Hunter Audit

**Audit date:** 2026-07-12
**Scope:** local scraper, matcher, storage, browser/application assistance, Flask admin panel, tests, documentation, secrets, and OpenTech compatibility.

## Executive verdict

Job-Hunter is **close to open-source-ready as a local, single-user, supervised tool**. It is **not ready as a hosted multi-user service**. The MIT license and community documents are already present, tests execute successfully, tracked-file secret hygiene is good, and Python syntax is clean. Release blockers are test/CI truthfulness and a sharper safety boundary around browser submission. Hosted mode additionally requires application authentication, CSRF protection, tenant isolation, upload hardening, and concurrency-safe persistence.

## Executed evidence

| Check | Result | Notes |
|---|---|---|
| Python syntax | Pass | 25 Python files parsed, 0 errors |
| Matcher + storage tests | Pass | 11 passed, 0 failed |
| Browser tests | Pass | 10 passed, 0 failed |
| Live API tests | Partial pass | 10 passed, 0 failed, 2 skipped because external prerequisites were unavailable |
| Secret scan | Pass for tracked tree | No high-confidence secret in tracked files; ignored local data remains outside this claim |
| Tracked personal/output data | Pass | Only profile initializer/example are tracked; `.env`, credentials, output, and personal profile files are ignored |
| CI | Fail | No GitHub Actions workflow enforces the test suite |
| Test isolation | Fail | Tests import active configuration, print a real profile identity, and can create output directories |
| Documentation consistency | Fail | Docs say 24 tests while default inventory is 27; contributing guide says no automated suite |
| Hosted-mode security | Fail | 33 Flask routes have no in-application authentication or CSRF protection |

## Release classification

### Local open-source release: conditional GO

Close the local P0 gates: isolate test profiles, add CI, prove dry-run never submits, correct documentation, and publish a clear automation/supervision policy.

### Hosted or multi-user release: NO-GO

External Nginx/basic authentication is not sufficient as the application security model for routes that create/delete profiles, upload/delete resumes, mutate job data, or execute profile configuration. Hosted mode must remain experimental/disabled by default until its separate gates are met.

## P0 local-release gates

1. Add CI that runs deterministic unit tests and an opt-in live integration job.
2. Use a synthetic test profile and temporary output directory; never import or print the active user's identity.
3. Add browser safety scenarios proving dry-run cannot submit and every submission requires a fresh, explicit confirmation.
4. Correct test counts and contributing documentation.
5. Document that profile Python files are trusted local code and are executed, not treated as inert data.

## P0 hosted-mode gates

- Add application authentication, authorization, CSRF, secure session/cookie defaults, and tenant ownership checks.
- Validate upload size, MIME and PDF magic; isolate files by tenant; add quotas and malware/content policy.
- Replace shared CSV read-modify-write with concurrency-safe persistence or locking plus atomic writes.
- Disable debug mode and add a production WSGI deployment path.

## Scope limitations

Live third-party API behavior is inherently unstable and two live cases were skipped. No real application was submitted. The audit did not test a public deployment or perform a complete Git-history secret scan.
