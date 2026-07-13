# AGENTS.md — Job-Hunter

Read this file before modifying the repository.

## Project identity

Job-Hunter is a local-first, two-phase job-search tool: it collects/matches opportunities, then assists a supervised user with application preparation. The default security profile is one trusted user on one local machine.

## Non-negotiable boundaries

1. Never submit an application without a fresh, explicit user confirmation for that exact job/page state.
2. Dry-run mode must be structurally unable to call a submit primitive.
3. Profiles, resumes, form answers, credentials, browser sessions, and history stay local unless the user explicitly enables a documented, field-level integration.
4. Treat profile `.py` files as trusted executable code. Do not accept them from untrusted hosted users.
5. Do not present the Flask admin server as hosted/multi-user-ready without application auth, authorization, CSRF, tenant isolation, hardened uploads, safe persistence, and a production WSGI path.
6. External job sources are unstable. Required CI uses deterministic fixtures; live checks are separate smoke tests.

## Repository guidance

- `README.md`, `SETUP_CHECKLIST.md`, and `docs/USER_GUIDE.md` describe user workflows.
- `TESTING.md` and `run_tests.py` define verification.
- `SECURITY.md` and `docs/OPEN_SOURCE_RELEASE_CHECKLIST.md` define release constraints.
- `docs/AUDIT.md` and `docs/GAP_AUDIT.md` record current evidence and gaps.
- Material proposals must follow `docs/PROPOSAL_CREATION_SOP.md` and `docs/proposals/TEMPLATE_PROPOSAL.md`.

## Coding and test rules

- Use synthetic identities and temporary directories in tests; never load the operator's active profile.
- Add regression tests for fixes and exercise production functions rather than duplicating their logic in tests.
- Keep secrets and personal/output files ignored. Update examples with placeholders only.
- Validate all profile names, filenames, URLs, uploaded files, and external payloads at trust boundaries.
- Use atomic/concurrency-safe persistence for paths touched by background scraping and UI mutations.
- Document executed evidence separately from inferred or proposed behavior.

## OpenTech integration

OpenTech may coordinate sanitized queue/status metadata. The local runner remains responsible for scraping and supervised browser actions. Do not send resumes, answers, credentials, cookies, local paths, or personal profile details. Integration must be optional, idempotent, bounded during outages, and unable to weaken the submission-confirmation rule.
