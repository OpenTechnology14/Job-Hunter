# Suggested Updates to Existing Documents

## `TESTING.md`

- Replace the stated 24-test count. The audited default inventory was 27 (API 7, matcher 4, storage 4, web 2, browser 7, config 3); preferably generate counts from collection instead of hardcoding them.
- Separate deterministic offline tests from live provider smoke tests and list required environment keys for the latter.
- Correct “no profile required”: current imports can load and print the active profile. After isolation work, document the synthetic fixture.
- Add dry-run non-submission, per-submit confirmation, temporary filesystem, CSV concurrency, and admin-route contract scenarios.

## `CONTRIBUTING.md`

Replace “No automated test suite yet” with the actual `run_tests.py` commands, explain deterministic versus live suites, and require tests for behavioral changes.

## `README.md`

- Add a release-profile statement: supported as a local, single-user, supervised tool; hosted/multi-user mode is experimental until the hosted gates close.
- State that profile `.py` files execute trusted local code.
- Link to the audit, open-source checklist, and supervision policy.
- Avoid implying universal source stability; third-party providers can change or throttle access.

## `SECURITY.md`

- Add an explicit deployed-mode warning and the current absence of in-app auth/CSRF/tenant isolation.
- Define supported versions and response expectations.
- Document sensitive data classes: profile identity, resume, form answers, job history, browser sessions, and API keys.

## `DEPLOY.md`

- Label the Flask debug server as development-only.
- Do not present external basic auth as sufficient for multi-user isolation.
- Add a hosted readiness gate that links to `docs/OPEN_SOURCE_RELEASE_CHECKLIST.md`.

## `HEALTH_CHECK.md`

Add checks for writable/atomic output storage, active-profile isolation, browser driver compatibility, source backoff state, and OpenTech adapter queue only when enabled.

## `SETUP_CHECKLIST.md`

Add a privacy review before using a real profile, a synthetic smoke-test option, and explicit confirmation that `.env`, credentials, profiles, resumes, and output are ignored.

## `APP_PLAYBOOK.md`

Define the supervision invariant precisely: fill/navigation can be assisted, but a submit action requires a fresh user confirmation and dry-run can never submit.
