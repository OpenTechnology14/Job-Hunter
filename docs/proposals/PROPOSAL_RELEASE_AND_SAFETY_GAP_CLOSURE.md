# Proposal: Release and Safety Gap Closure

**Status:** Ready for local-release implementation; hosted track requires Decision JH-D01
**Date:** 2026-07-12
**Release profile:** Local single-user first; hosted mode quarantined until separately proven
**Evidence:** JH-001 through JH-014 verified in `docs/AUDIT.md` and `docs/GAP_AUDIT.md`

## 1. Executive summary

Close the audited release and safety gaps without weakening Job-Hunter's defining boundary: it is a local tool that assists a human but does not make an unattended submission decision.

The first releasable increment produces deterministic CI, synthetic test isolation, atomic local persistence, explicit application outcomes, and direct tests proving that dry-run never submits and confirmations cannot be reused. The existing deployed/multi-user mode is disabled for production use until the project either removes it or completes the separate hosted-security track.

## 2. Relationship to the current OpenTech proposal

`PROPOSAL_OPENTECH_INTEGRATION_READINESS.md` owns the optional sanitized OpenTech client, outbox, template, and workflow hooks. This proposal is a prerequisite: OpenTech hooks must not be added until test isolation and application outcome semantics are complete. OpenTech cannot turn a `reviewed_manual` or `prepared` outcome into `submitted`.

## 3. Verified current state

- `run_tests.py` combines required logic tests with live HTTP/browser checks. Its default inventory is 27 although `TESTING.md` says 24.
- The comment claiming prevention of real-profile loading does not actually set a synthetic profile or isolate the filesystem before dependent imports.
- `config.py` defaults to the personal profile name `alex`, executes a profile module, creates output directories, and prints identity/config at import time.
- `browser_apply.py::handle_easy_apply` checks dry-run before its own submit click, but the safety invariant is not tested directly.
- `browser_apply.py::handle_form_apply` returns success after the user says review is done even though Job-Hunter did not itself submit. This conflates “reviewed/manual” with “submitted.”
- `admin/server.py::_write_csv` writes directly to the destination. Job PATCH/bulk and scrape processes can race and lose updates or leave a partial file.
- Profile names and resume paths are assembled from route values; sanitization/containment is not centralized.
- Resume upload checks only a `.pdf` suffix and sanitized filename; it has no size, MIME, PDF-signature, quota, or collision policy.
- Deployed mode exposes profile/resume/job mutations and executes Python profile source without in-application auth, authorization, CSRF, or tenant isolation.
- `app.run(..., debug=True)` is unconditional.
- MIT licensing and the community/governance documents already exist.

## 4. Goals, non-goals, and decision gate

### Gap ownership matrix

| Gap | Owning work package | Closure outcome |
|---|---|---|
| JH-001 | JH-WP1 | Enforced deterministic CI |
| JH-002 | JH-WP1 | Synthetic profile and temporary filesystem isolation |
| JH-003 | JH-WP2 | Non-bypassable dry-run and per-submit confirmation guard |
| JH-004 | JH-WP0/JH-WP1 | Accurate generated test documentation |
| JH-005 | JH-WP1 | Required offline tests separated from live smoke |
| JH-006 | JH-WP0/JH-WP6 | Deployed mode removed or authenticated |
| JH-007 | JH-WP0/JH-WP6 | Mutations unavailable in hosted mode or protected by CSRF |
| JH-008 | JH-WP0/JH-WP6 | Hosted executable profiles removed or hosted mode removed |
| JH-009 | JH-WP4 | Bounded, verified, contained PDF upload |
| JH-010 | JH-WP3 | Atomic locked persistence and stable revisions |
| JH-011 | JH-WP0/JH-WP4/JH-WP6 | Debug-off app factory and supported production disposition |
| JH-012 | JH-WP5 | Optional sanitized OpenTech integration |
| JH-013 | JH-WP4 | Contract decision/test mapped to every Flask route |
| JH-014 | JH-WP1 | Tests exercise production logic directly |

### Goals

- Make the default test command deterministic, offline, synthetic, and CI-enforced.
- Establish a testable submission guard that no adapter can bypass.
- Represent `prepared`, `reviewed_manual`, `submitted`, `skipped`, and `failed` distinctly.
- Make local CSV/JSON writes atomic and concurrency-safe.
- Centralize safe profile/filename/path validation and harden local uploads.
- Prevent users from mistaking deployed mode for a supported hosted service.
- Correct all stale user/contributor/security/deployment documentation.

### Non-goals

- Guaranteeing availability or terms compatibility of third-party sources.
- Automating CAPTCHA, bypassing access controls, or evading provider rate limits.
- Sending applications unattended.
- Sending private profile/resume/form/browser data to OpenTech.
- Rewriting the local-first CLI as a cloud service.

### Decision JH-D01 — disposition of deployed mode

Choose before hosted work begins:

1. **Remove/deprecate deployed mode (recommended):** delete multi-user UI/API claims and retain loopback single-user admin. This closes JH-006 through JH-011 for the supported release by removing that release profile.
2. **Retain and secure hosted mode:** implement the full Hosted Track in section 11 before enabling it.

Until the decision is complete, `--deployed` must refuse to start with a message linking to this proposal. An `unsafe` override is not part of the supported release.

## 5. Target repository structure

```text
requirements-dev.txt
.github/workflows/ci.yml
tests/
  conftest.py
  unit/
  contract/
  scenarios/
  fixtures/
    profiles/synthetic.json
    sources/
job_hunter/
  application/
    outcomes.py
    submission_guard.py
  persistence/
    atomic.py
  validation/
    paths.py
```

Existing top-level imports may remain compatible through small re-exports. A full package migration is not required in the first pull request.

## 6. Direct injection map

| Gap | Location | Symbol/surface | Implementable change | Verification |
|---|---|---|---|---|
| JH-001/005 | `requirements-dev.txt` (new), `.github/workflows/ci.yml` (new) | required offline job, optional live job | Pin pytest/Ruff; run offline suite on supported Python; schedule/manual live provider smoke | Deliberate failure blocks; offline job has no network/profile secrets |
| JH-001/005 | `run_tests.py` | argument grouping | Make default run deterministic groups only; add explicit `--live-api` and `--live-browser`; retain old flags with deprecation messages | CLI contract tests |
| JH-002 | `config.py` | `_get_profile_name`, `_load_profile`, import side effects | Default to `example_profile` or require explicit profile for real runs; move directory creation/printing into `initialize_runtime()` | Import test creates no dirs and prints no identity |
| JH-002 | `tests/conftest.py` (new) | `synthetic_runtime` fixture | Set temp output root, synthetic profile/config, patched argv/env before app imports | Privacy scan and filesystem assertion |
| JH-003 | `job_hunter/application/submission_guard.py` (new) | `SubmissionGuard` | Issue one short-lived confirmation for job ID + page fingerprint; consume once; deny dry-run structurally | Unit/property tests |
| JH-003 | `browser_apply.py` | `handle_easy_apply`, `handle_form_apply`, `apply_to_job` | Route submit click through guard; return typed outcome; generic form returns `reviewed_manual`, never `submitted` | Adapter scenarios with fake page/click recorder |
| JH-004 | `TESTING.md`, `CONTRIBUTING.md` | test commands/counts | Remove hardcoded count or generate collection summary; document deterministic/live split | Docs command smoke test |
| JH-006–011 | `admin/server.py` | startup/`DEPLOYED_MODE` | Quarantine `--deployed` until JH-D01; never imply multi-user support from UI mode alone | Startup test refuses deployed mode |
| JH-009 | `admin/server.py` and `job_hunter/validation/paths.py` | upload/download/delete helpers | Validate profile ID, resolve containment, cap body/file size, verify PDF magic/MIME, reject collisions or create safe unique name | Upload/path traversal matrix |
| JH-010 | `job_hunter/persistence/atomic.py` (new) | `locked_update_csv`, `atomic_write_json` | Per-file lock, write+fsync temp in same directory, `os.replace`, cleanup on error | Concurrent writer and kill/fault tests |
| JH-010 | `admin/server.py`, `local_sync.py`, `run_scrape_browsers.py`, `ai_training.py` | direct writes/read-modify-write | Use shared atomic helpers for files mutated by UI/background processes | No direct unsafe write in audited paths |
| JH-011 | `admin/server.py` entry point | Flask startup | Debug only through explicit local development flag; add `create_app()` for testing/WSGI | Test client import has no server side effect |
| JH-012 | OpenTech proposal locations | integration | Implement only after JH-001–005/010 close | Existing OTJ matrix |
| JH-013 | `tests/contract/test_admin_routes.py` (new) | 33-route ledger | Add success, validation, missing-object, path and mutation coverage; hosted auth cases only if retained | Ledger maps every route to tests |
| JH-014 | matcher/storage tests | duplicated logic | Import production salary/matching/dedupe functions; delete inline clones | Mutation/regression test fails when production changes |

## 7. Submission safety contract

### 7.1 Typed outcomes

```python
class ApplyState(str, Enum):
    PREPARED = "prepared"
    REVIEWED_MANUAL = "reviewed_manual"
    SUBMITTED = "submitted"
    SKIPPED = "skipped"
    FAILED = "failed"

class ApplyOutcome(BaseModel):
    state: ApplyState
    job_id: str
    resume_used: str | None = None
    reason_code: str | None = None
```

If Pydantic is not adopted for core local models, use a frozen dataclass with equivalent serialization. `SUBMITTED` is valid only when Job-Hunter observed its guarded submit click succeed. Manual review is never rewritten as submitted.

### 7.2 Guard behavior

```python
guard = SubmissionGuard(dry_run=dry_run)
token = guard.request_confirmation(
    job_id=job_id,
    page_fingerprint=current_page_fingerprint(page),
)
guard.submit_once(token, lambda: submit_button.click())
```

Required invariants:

- `dry_run=True` cannot mint a token or invoke the callback.
- A token is scoped to one job and one page fingerprint.
- A token expires within a short configured window and is consumed exactly once.
- navigation, reload, detected job change, failure, or cancellation invalidates it.
- no other function may click an element classified as Submit.

The first “Easy Apply found” prompt authorizes navigation into the form, not submission. The second guarded confirmation authorizes one click only.

## 8. Test isolation and command contract

### Default required command

```bash
python -m pytest -m "not live and not browser_live"
```

It must run without network, Playwright browser installation, API keys, personal profiles, resumes, credentials, or existing `output/` content.

### Live commands

```bash
python -m pytest -m live
python -m pytest -m browser_live
```

Live jobs are scheduled/manual, report provider failures separately, and do not block a local patch release unless the changed provider is in the declared release scope. Recorded provider fixtures remain required.

### Import behavior

`import config` and `create_app()` must not:

- create directories;
- print profile name, user name, email, or paths;
- load a personal default;
- start a server or subprocess.

Entry points call `initialize_runtime(profile_name, output_root)` explicitly after argument validation.

## 9. Atomic persistence contract

```python
def locked_update_csv(path: Path, columns: list[str], mutate):
    with FileLock(f"{path}.lock", timeout=10):
        rows = read_csv(path)
        new_rows = mutate(rows)
        atomic_write_csv(path, new_rows, columns)
        return new_rows
```

`atomic_write_csv/json` writes to a unique temporary file in the destination directory, flushes and fsyncs, preserves safe permissions, calls `os.replace`, and removes residue on failure. The lock covers the entire read-modify-write transaction, not only the final write.

API updates should stop addressing mutable rows solely by list index. Add a stable `Job ID` derived from normalized source plus canonical URL. During compatibility, accept `index` but return an `ETag`/revision and reject stale updates with `409 conflict`.

## 10. Local admin hardening

Even when bound to loopback:

- centralize `validate_profile_id()` with `^[a-z0-9][a-z0-9_-]{0,63}$`;
- resolve every profile/resume path and confirm it remains under the configured output root;
- set `MAX_CONTENT_LENGTH` (proposed default 5 MiB, configurable);
- require `.pdf`, `application/pdf`/`application/octet-stream` as appropriate, and `%PDF-` file signature;
- generate downloads with safe content disposition and `nosniff` headers;
- reject overwrite by default and expose an explicit replace action;
- use `create_app(config)` and `debug=False` by default;
- return stable JSON errors: `invalid_profile`, `invalid_filename`, `file_too_large`, `invalid_pdf`, `conflict`, `busy`, `not_found`.

These controls do not make the app multi-user-ready; they reduce local accidents and prepare contract tests.

## 11. Hosted track if JH-D01 retains deployed mode

This entire section is one release gate. Partial completion must not enable hosted mode.

### Architecture

- Replace executable hosted profile `.py` files with a versioned declarative schema stored in SQLite/Postgres.
- Add an app factory and production WSGI server configuration.
- Add session authentication with password hashing or a documented trusted identity proxy whose verified identity is passed securely.
- Add CSRF protection for cookie-authenticated mutations.
- Associate every profile, job, resume, role, history record, scrape operation, and outbox event with an owner/tenant ID.
- Authorize every object lookup before revealing existence.
- Use database transactions/optimistic revisions for hosted mutations.
- Add quotas, rate limits, secure cookies/headers, audit events, retention/export/deletion, and backup/restore.

### Exact injection points

| Location | Change |
|---|---|
| `admin/server.py` | Reduce to `create_app()` composition; register auth, profile, job, resume, scrape blueprints |
| `admin/auth.py` (new) | Login/logout/session identity and `require_user`/`require_admin` decorators |
| `admin/csrf.py` (new or framework integration) | Token creation/validation and JSON mutation handling |
| `admin/models.py` (new) | User, Profile, Job, Resume, Role, Operation, AuditEvent with owner IDs/revisions |
| `admin/services/uploads.py` (new) | Streaming validation, quota, tenant path/storage abstraction |
| `admin/migrations/` (new) | Versioned schema and local trusted-profile import tool |
| every `/api/*` route | Object-scoped authorization, validation, stable errors, audit event |
| `requirements.txt`/deployment files | WSGI server, auth/CSRF/database dependencies and locked versions |

### Hosted acceptance gate

- Anonymous access is denied except explicit health/login/static routes.
- User A cannot enumerate, read, update, delete, scrape, download, or infer User B resources.
- Cross-site mutations fail.
- Uploaded polyglot/oversized/traversal files fail safely.
- Profile input cannot execute Python or template expressions.
- Concurrent mutations have transaction/revision semantics.
- Debug is off; TLS/proxy/security headers and session cookies pass configuration tests.
- Backup/restore and account data deletion are exercised.

## 12. Work packages and implementation order

### JH-WP0 — Quarantine unsupported claims

Disable deployed startup, correct README/DEPLOY/SECURITY language, and fix the test count/no-profile claim.
**Exit:** a local user cannot accidentally start an unsupported hosted mode.

### JH-WP1 — Deterministic test foundation

Add dev dependencies, pytest structure, synthetic runtime fixture, recorded provider fixtures, and CI. Retain `run_tests.py` temporarily as a compatibility wrapper.
**Exit:** required CI runs offline with no personal output and fails on zero collected tests.

### JH-WP2 — Submission safety and outcomes

Add the guard/outcome modules, refactor browser functions, and add fake-page scenarios.
**Exit:** dry-run and confirmation invariants pass; manual review is not reported as submission.

### JH-WP3 — Persistence and stable IDs

Add atomic/locked helpers, migrate direct writes in audited paths, add stable Job ID and revision compatibility.
**Exit:** concurrency and fault-injection scenarios pass with no corrupt/lost update.

### JH-WP4 — Local admin contracts

Add app factory, path/upload validation, stable errors, route-ledger tests, and non-debug startup.
**Exit:** all 33 routes have mapped local contract evidence.

### JH-WP5 — OpenTech integration

Implement the existing OpenTech proposal after WP1–WP4.
**Exit:** OTJ-01 through OTJ-10 pass without changing submission semantics.

### JH-WP6 — Hosted disposition

Remove deployed mode or complete every hosted gate.
**Exit:** documentation and code expose only supported release profiles.

## 13. Scenario and pressure matrix

| ID | Scenario | Level | Expected result | Gate |
|---|---|---|---|---|
| GAP-JH-01 | Import config/app in empty temp directory | Unit | No output, identity print, directory, server, or subprocess | P0 |
| GAP-JH-02 | Default test command with network denied | CI | Deterministic suite passes | P0 |
| GAP-JH-03 | Zero tests collected | CI meta-test | Job fails | P0 |
| GAP-JH-04 | Dry-run reaches visible Submit | Safety | No token/click; outcome not submitted | P0 |
| GAP-JH-05 | Reuse confirmation on second job/page | Safety | Guard rejects | P0 |
| GAP-JH-06 | Generic form reviewed manually | Contract | `reviewed_manual`, never `submitted` | P0 |
| GAP-JH-07 | Two writers update different jobs | Concurrency | Both changes persist or one receives conflict | P0 |
| GAP-JH-08 | Fault before `os.replace` | Recovery | Original file intact; temp cleaned | P0 |
| GAP-JH-09 | Profile/resume traversal strings | Contract | `400`, no external path access | P0 |
| GAP-JH-10 | Oversized/fake PDF | Contract | Rejected with no residue | P0 |
| GAP-JH-11 | Start `--deployed` before disposition | Startup | Refuses with clear remediation | P0 |
| GAP-JH-12 | Every local API route valid/invalid request | Contract | Stable documented response | P1 |
| GAP-JH-13 | Cross-user route matrix (if hosted retained) | Security | Denied without existence leak | Hosted P0 |
| GAP-JH-14 | OpenTech offline/replay/private field | Integration | Bounded/idempotent/sanitized; local path unaffected | P1 |

## 14. Rollout and rollback

- Merge JH-WP0/1 first; they change claims and tests, not user data.
- Ship safety outcomes with a compatibility serializer that maps only observed `submitted` to legacy Done. Preserve original CSV before the first schema change.
- Introduce stable Job ID/revision columns additively; support legacy rows until one documented migration has completed.
- Enable the atomic store for one profile fixture, then all local profiles after backup/restore tests.
- Keep OpenTech disabled by default.

Rollback disables OpenTech, restores the prior local adapter behind a short-lived feature flag only if it does not weaken submission safety, and restores CSV from the pre-migration backup. Never roll back the dry-run guard, path containment, or debug-off default.

## 15. Definition of done

- JH-001 through JH-005, JH-010, JH-013, and JH-014 have linked automated evidence for the local release.
- JH-006 through JH-011 are closed either by removing hosted mode from the supported product or by completing the entire Hosted Track.
- No default test accesses a live provider, personal profile, resume, credential, or persistent output directory.
- No code path can classify manual review as observed submission.
- No submit click bypasses `SubmissionGuard`.
- Audited CSV/JSON mutations are atomic and concurrency-safe.
- All 33 Flask routes map to a contract decision/test or are removed.
- README, testing, contributing, security, deployment, setup, health, playbook, route ledger, gap audit, and release checklist match the implementation.
