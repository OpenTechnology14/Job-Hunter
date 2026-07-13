# Gap Audit

Implementation sequence, file-level changes, safety contracts, and release gates are defined in [the release and safety gap-closure proposal](proposals/PROPOSAL_RELEASE_AND_SAFETY_GAP_CLOSURE.md).

| ID | Priority | Gap | Direct injection location | Acceptance evidence |
|---|---|---|---|---|
| JH-001 | P0 local | No enforced CI | `.github/workflows/ci.yml` | Unit suite runs on supported Python matrix; failure blocks merge |
| JH-002 | P0 local | Tests load real active profile | `config.py`, `run_tests.py`, web/config tests | Synthetic fixture only; no personal identity/output side effects |
| JH-003 | P0 local | Submission safety not proven | `browser_apply.py`, browser tests | Dry-run has zero submit calls; each actual submit needs fresh confirmation |
| JH-004 | P0 local | Stale docs/test count | `TESTING.md`, `CONTRIBUTING.md` | Count generated or omitted; commands match runner |
| JH-005 | P0 local | Live and deterministic tests mixed | `run_tests.py`, API/browser test modules | Offline default is deterministic; live suite is explicit and tolerant of provider drift |
| JH-006 | P0 hosted | No app authentication/authorization | `admin/server.py` app factory and all `/api/*` routes | Auth, role and object-ownership tests |
| JH-007 | P0 hosted | No CSRF protection | Mutating admin routes | Cross-origin mutation is rejected; same-origin token flow passes |
| JH-008 | P0 hosted | Profile files execute Python | Profile loader and create/upload paths | Hosted profiles use declarative schema; no arbitrary code execution |
| JH-009 | P0 hosted | Upload validation incomplete | `/api/resumes/<profile>/upload` | Size, MIME, magic, filename, quota and ownership tests |
| JH-010 | P0 hosted | CSV lost-update risk | storage helpers and job PATCH/scrape paths | Atomic write/locking or database transaction concurrency test |
| JH-011 | P0 hosted | Debug dev server is unconditional | `admin/server.py` entry point | Production WSGI command; debug false; proxy/security config documented |
| JH-012 | P1 | OpenTech handoff absent | new local adapter/runner, config example | Sanitized idempotent job/status ingestion with offline recovery |
| JH-013 | P1 | No API contract tests for 33 routes | `tests/admin/` | Success/auth/validation/not-found/conflict coverage per mutating route |
| JH-014 | P2 | Matching rules duplicated in tests | matcher test module | Tests exercise exported production functions |

Local release work must not accidentally imply hosted readiness. Track and label the two release profiles separately.
