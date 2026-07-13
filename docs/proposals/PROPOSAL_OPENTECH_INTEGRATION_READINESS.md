# Proposal: OpenTech Integration and Release Readiness

**Status:** Draft
**Date:** 2026-07-12
**Release profile:** Local single-user first; hosted mode excluded
**Evidence:** Job-Hunter state verified; integration proposed

## 1. Executive summary

Add a local Job-Hunter runner that can synchronize sanitized job workflow state with an OpenTech Job Hunter project template. OpenTech becomes the planning/review UI; Job-Hunter remains the local executor for scraping, matching, resume selection, browser navigation, and supervised form filling. Submissions always remain under direct user control.

## 2. Verified current state

- Job-Hunter has working local source, matching, storage, browser, and configuration tests, but no enforced CI.
- It stores sensitive profiles, resumes, form answers, history, and credentials locally and ignores them in Git.
- The Flask admin surface has 33 routes and no in-app auth/CSRF; this proposal does not expose it publicly.
- OpenTech has a Job Hunter template and queue-ingest concept, while Job-Hunter has no current adapter.
- Existing template/proposal material expects a local runner for scraping/apply capabilities that the web UI should not perform.

## 3. Goals and non-goals

### Goals

- Make OpenTech the optional queue/status/review surface for local Job-Hunter runs.
- Preserve local storage and explicit submission confirmation.
- Add deterministic CI and safety tests needed for a public local release.
- Make synchronization idempotent, recoverable, and private by construction.

### Non-goals

- Hosting the Flask admin server as a public multi-user service.
- Uploading resumes, form answers, credentials, browser state, or full profile data to OpenTech.
- Letting OpenTech or any unattended task submit an application.
- Replacing Job-Hunter's source adapters with remote browser automation.

## 4. User paths

1. User imports/creates the OpenTech Job Hunter project and copies a project/queue identifier.
2. Local setup validates Job-Hunter configuration and optionally tests the OpenTech endpoint with a synthetic event.
3. A scrape/match run creates or updates sanitized queue items.
4. User selects an item for local preparation. The runner resolves private profile/resume/form data locally.
5. Browser assistance navigates/fills. Immediately before any submit action, the local UI asks for a fresh confirmation.
6. Completion/failure status is synchronized. During an outage, a bounded local outbox retries idempotently.
7. Disconnecting clears unsent events and leaves local job/history data intact.

## 5. Architecture and data flow

```text
OpenTech Job Hunter template
     ^ sanitized status/tasks
     | HTTPS, opt-in, idempotent
Local Job-Hunter adapter/outbox
     |
scrapers -> matcher -> local CSV/profile/resume -> supervised browser
```

Allowed outbound fields: stable opaque job ID, company, title, public job URL, public source, coarse location, workflow status, timestamps, safe error reason, and aggregate match band if enabled. Forbidden: name/contact details, resume bytes/path, form answers, credentials/tokens, cookies/session state, demographic answers, salary preferences unless explicitly selected, local filesystem paths, and browser screenshots.

## 6. Direct injection map

| Location | Symbol/surface | Proposed change | Example | Verification |
|---|---|---|---|---|
| `integrations/opentech/client.py` (new) | `OpenTechClient.ingest()` | Typed timeout/retry client with idempotency header | request below | Fake-server contract tests |
| `integrations/opentech/sanitize.py` (new) | `to_queue_item()` | Field allow-list and stable opaque ID | forbidden-field rejection | Property/privacy tests |
| `integrations/opentech/outbox.py` (new) | local outbox | Atomic bounded retry queue | max age/count config | Crash/replay/outage tests |
| `config.example.py` or `.env.example` | integration settings | Disabled default; endpoint/project/queue and secret reference | `OPENTECH_ENABLED=false` | Config validation |
| scrape orchestration entry point | post-persist hook | Enqueue sanitized upserts after local save | one batch/event | Duplicate and partial-failure tests |
| `browser_apply.py` | completion/failure hook | Emit status only after local terminal state | no private form data | Safety/redaction tests |
| `run_tests.py` | `--opentech` group | Add offline client/sanitizer/outbox suite | required in CI | Collection/count test |
| `.github/workflows/ci.yml` (new) | offline test job | Synthetic profile/temp filesystem; live smoke separate | Python matrix | Deliberate failure gate |
| OpenTech template | Job Hunter template JSON | Remove personal examples; add runner setup/status/review fields | generic fixture | Import/schema test |

## 7. Contracts and examples

### OpenTech ingestion request

```http
POST /api/queues/{queueId}/ingest
Authorization: Bearer <token>
Idempotency-Key: jh:job_7f2a:status:matched:v3
Content-Type: application/json
```

```json
{
  "source": "job-hunter-local",
  "items": [
    {
      "external_id": "job_7f2a",
      "title": "Software Engineer",
      "company": "Example Company",
      "source": "lever",
      "public_url": "https://jobs.example/job/123",
      "location": "Remote",
      "status": "matched",
      "match_band": "strong",
      "updated_at": "2026-07-12T18:00:00Z"
    }
  ]
}
```

### Local runner status

```json
{
  "runner_version": "0.x",
  "connected": true,
  "outbox_depth": 0,
  "last_sync_at": "2026-07-12T18:00:02Z",
  "supervision": "required_for_submit"
}
```

Stable errors: `invalid_config`, `unauthorized`, `rate_limited`, `endpoint_unavailable`, `payload_rejected`, `privacy_field_rejected`, `outbox_full`. Logs must not include authorization values or rejected private field values.

## 8. Security, privacy, and supervision

- Integration is disabled by default and limited to an allow-listed HTTPS origin outside local test mode.
- Token storage uses an environment/OS secret reference and is never returned by `/api/setup`.
- The outbox is permission-restricted and stores only already-sanitized payloads.
- Dry-run cannot call any submit primitive. Confirmation is scoped to one job, one page state, and a short expiry; navigation invalidates it.
- OpenTech “Apply” means “open a supervised local preparation task,” never remote submission.

## 9. Test and pressure matrix

| ID | Scenario | Type | Expected result | Gate |
|---|---|---|---|---|
| OTJ-01 | Integration disabled | Deterministic | Zero outbound requests/outbox records | P0 |
| OTJ-02 | Synthetic upsert | Contract | One valid generic queue item | P0 |
| OTJ-03 | Private fields injected | Privacy | Rejected/dropped; values absent from logs/outbox | P0 |
| OTJ-04 | Same event replayed | Contract | One logical update | P0 |
| OTJ-05 | Endpoint offline/recovery | Pressure | Bounded retry and ordered recovery | P1 |
| OTJ-06 | Crash during outbox write | Recovery | Valid old or new record; no corrupt state | P0 |
| OTJ-07 | Dry-run on every apply adapter | Safety | Zero submit calls | P0 |
| OTJ-08 | Confirm first of two jobs | Safety | Second job cannot reuse confirmation | P0 |
| OTJ-09 | Real profile absent in CI | Isolation | Synthetic tests pass with no personal output | P0 |
| OTJ-10 | Provider API changes | Live smoke | Visible provider failure; integration/local data preserved | P1 |

## 10. Delivery plan

1. **Release truth:** fix test isolation/docs and add offline CI plus submission invariants.
2. **Sanitizer/client:** implement typed allow-list and fake-server contract tests.
3. **Atomic outbox:** bounded queue, retry/backoff, crash recovery, operator status.
4. **Workflow hooks:** sync scrape/match/preparation/terminal status behind a disabled-default flag.
5. **OpenTech template:** genericize examples, document runner setup, add readiness/status/review tasks.
6. **Alpha:** opt-in local users, metrics limited to local logs, rollback rehearsal.

## 11. Rollout and rollback

Start with synthetic endpoint tests, then a private OpenTech project. Roll back by setting `OPENTECH_ENABLED=false`, deleting the sanitized outbox, and revoking the token. No local job/profile/resume data is removed and scraping/matching/browser assistance remains available.

## 12. Risks and unresolved decisions

| Item | Decision owner |
|---|---|
| Exact OpenTech ingest schema/version compatibility | OpenTech API owner |
| Whether coarse location and match band are enabled by default | Privacy/product owner |
| Outbox maximum count/age | Maintainer |
| Token storage mechanism by OS | Security/desktop owner |
| Long-term CSV vs SQLite persistence | Job-Hunter maintainer |

## 13. Existing-document updates

Update the README, setup checklist, testing guide, security policy, health check, app playbook, source list, OpenTech template README, and API documentation as each phase ships. Do not document the integration as available before the adapter and template import tests pass.
