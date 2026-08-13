# Proposal: Standalone Workflow and OpenTech Template Testing

**Status:** Draft — starting scaffold, not a feature proposal
**Date:** 2026-08-12
**Release profile:** Local single-user
**Evidence:** Verified against current repo state; test scenarios not yet written

## Purpose

This is the **starting doc**, not a finished one. It exists to become the shared workflow/testing-scenario doc between this repo and OpenTech's `job_hunter` project template — built out together as the standalone system and the template connection both evolve. Don't treat any checklist below as executed until it's checked off with real evidence.

This is deliberately narrower than [`PROPOSAL_OPENTECH_INTEGRATION_READINESS.md`](PROPOSAL_OPENTECH_INTEGRATION_READINESS.md), which owns the integration *architecture* (data flow, privacy boundary, sync contract). This doc owns the *operational workflow* — how you actually run the thing, standalone and connected — and the test scenarios that prove it works. Update the architecture proposal for design changes; update this one as you run and verify each path.

## 1. Standalone workflow (no OpenTech involved)

As it exists today, per `CONTRIBUTING.md` and `CLAUDE.md`:

1. **Setup:** `python3 -m venv venv && pip install -r requirements.txt && playwright install chromium`. Copy `profiles/example_profile.py` to a per-person profile file (pure Python data — no imports, no side effects, gitignored).
2. **Scrape:** `run_scrape.py` (API sources: Greenhouse, Lever, Himalayas, RemoteOK, USAJobs, Arbeitnow, Workday, The Muse, Wellfound, Adzuna, Google Jobs) and/or `run_scrape_browsers.py` (LinkedIn/Indeed via Playwright). Results land in `output/{profile}/jobs.csv` and `browser_jobs.csv`.
3. **Match:** `matcher.py` does keyword + salary matching (no AI) against the profile's `ROLE_PROFILES`/`SEARCH_SETTINGS`.
4. **Review:** the Flask admin panel (`admin/server.py`, `localhost:5175`, single-page dashboard, no build step) is where a human reviews matched jobs, resume selection (`resume_picker.py` maps role category → resume PDF), and run history.
5. **Apply:** `run_apply.py` drives `browser_apply.py` (Playwright form-fill) for API-sourced eligible jobs. `--dry-run` opens the browser without submitting. LinkedIn/Indeed results are manual-apply only (`browser_jobs.csv`).
6. **Data stays local:** profiles, resumes, form answers, and run history are gitignored and never leave the machine in this mode.

## 2. Connected workflow (via the OpenTech `job_hunter` template)

Per [`PROPOSAL_OPENTECH_INTEGRATION_READINESS.md`](PROPOSAL_OPENTECH_INTEGRATION_READINESS.md)'s design (architecture, not yet built): OpenTech becomes the planning/review UI over a sanitized queue; this repo remains the local executor. Only opaque job ID, company, title, public URL, source, coarse location, workflow status, timestamps, and safe error reasons cross the wire — never resume bytes, form answers, credentials, or filesystem paths. Every submit action requires a fresh local confirmation regardless of connection state.

On the OpenTech side, the counterpart is the `job_hunter` built-in project template (`src/lib/templates.ts` in `Task-Management`), currently tracked at `JOB-06` in that repo's `PRIORITY.md` — a stub walkthrough doc lives at `Task-Management/docs/runbooks/PROJECT_TEMPLATE_TESTING.md#job-hunter-job_hunter`, to be filled in from both sides together.

## 3. Test scenarios — stub, to be built together

Split the same way the workflow is split above. Nothing here is written yet; fill in real scenarios as each piece gets built/verified, and record actual results (pass/fail/date), not just the scenario description.

### Standalone only

- [ ] Fresh profile setup → scrape → match → admin panel review, end to end, one profile.
- [ ] Dry-run apply opens the browser and fills the form without submitting.
- [ ] A real (supervised) apply submits and updates `run_log.json`.
- [ ] Multi-profile isolation: two profiles' data never cross in `output/`.

### Via the OpenTech connection (once the adapter/outbox from `PROPOSAL_OPENTECH_INTEGRATION_READINESS.md` exists)

- [ ] A scrape/match run creates sanitized queue items visible in the OpenTech `job_hunter` template.
- [ ] Selecting a queue item in OpenTech resolves the corresponding private data *locally only* — no private field ever appears in an OpenTech request/response.
- [ ] Submit confirmation happens locally even when the run was initiated from OpenTech.
- [ ] Outage: OpenTech unreachable mid-run — local outbox retries idempotently, no duplicate submissions, no data loss.
- [ ] Disconnecting the integration clears the unsent outbox and leaves local job/history data intact.

## 4. How to keep this doc alive

- When you build a piece of the connection, move its scenario from "stub" to a real pass/fail with a date and what you actually did.
- When the standalone workflow changes (new source, new admin panel feature), update §1 first — this doc should always describe what's actually running, not what's planned.
- Cross-link new findings back into `PROPOSAL_OPENTECH_INTEGRATION_READINESS.md` if they change the architecture, not just this doc.
