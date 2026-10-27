# Suggested Updates to Existing Documents

## `TESTING.md`

*Done 2026-10-23: hardcoded count removed, deterministic/live split documented, "no profile required" corrected, dry-run and confirmation scenarios added (§14).* Still open:

- List the required environment keys for the live smoke tests.
- Add temporary-filesystem, CSV-concurrency and admin-route contract scenarios once those tests exist.

## `CONTRIBUTING.md`

*Done 2026-10-23.*

## `README.md`

- *Done 2026-10-23:* release-profile statement, trusted-code note, audit link.
- Link to the open-source checklist and supervision policy.
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
