# Full Application Audit Matrix

| Surface | Evidence | Status | Next proof |
|---|---|---|---|
| Source adapters | Live API tests with two skips | Partial | Recorded fixtures plus opt-in live smoke |
| Job matcher | 4 tests calling production functions (2026-10-26) | Implemented | Mutation-tested; broader rule coverage |
| CSV storage | 4 tests | Local implemented | Atomic/concurrent update test |
| Web parsing | 2 tests | Implemented helper | Fixture corpus and provider drift cases |
| Browser automation | 7 default tests plus config cases; 3 offline fake-page safety tests (2026-10-23): dry-run never clicks Submit, live Submit needs confirmation | Experimental | Single-use per-job confirmation token (GAP-JH-05) and typed outcomes (GAP-JH-06) |
| Scrape CLI | Documented and exercised indirectly | Local implemented | Clean synthetic end-to-end fixture |
| Flask admin UI | 33 routes, manual docs | Local experimental | Route contract suite |
| Profile management | Python profile modules | Trusted-local only | Declarative model before hosting |
| Resume storage/upload | Local filesystem | Local experimental | Limits/type checks/tenant ownership |
| Deployment | Local plus proxy guidance | Local documented | Production WSGI and security acceptance |
| Health/maintenance | Root documents present | Documented | Automated smoke and backup/restore exercise |
| Test runner | 32 tests in all; the default run is 16 offline tests (2026-10-26). Synthetic profile and temp cwd; CI on Python 3.10–3.12 | Implemented | Required-check setting (JH-D05); recorded provider fixtures (JH-005) |
| Open-source governance | MIT, contribution, security, code of conduct | Strong | Release checklist/sign-off |
| OpenTech integration | No bridge in this repository | Proposed | Local runner and ingest contract tests |

## Interpretation

“Trusted-local” means the operator controls the files and machine. It must not be reused as a hosted security argument. A feature becomes hosted-ready only after authentication, tenant isolation, concurrency, and abuse controls are proven.
