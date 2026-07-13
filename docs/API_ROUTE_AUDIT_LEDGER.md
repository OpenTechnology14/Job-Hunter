# Flask API Route Audit Ledger

All routes are defined in `admin/server.py`. At audit time there was no in-application authentication, authorization, or CSRF enforcement. The local server binds to `127.0.0.1`, which reduces exposure but does not make the route set safe for hosted mode.

| Method | Path | Operation | Hosted risk/gate |
|---|---|---|---|
| GET | `/` | Admin UI | Authenticated session if hosted |
| GET | `/static/<path:filename>` | Static asset | Path and cache policy |
| GET | `/api/profiles` | List profiles | Tenant-scoped metadata |
| GET | `/api/profiles/<name>` | Profile detail | Ownership; redact private fields |
| GET | `/api/profiles/<name>/location` | Profile location | Sensitive-data minimization |
| PATCH | `/api/profiles/<name>/search-settings` | Change search config | Auth, CSRF, schema, ownership |
| GET | `/api/jobs/<profile>` | List jobs | Ownership, pagination, safe CSV parsing |
| PATCH | `/api/jobs/<profile>/<int:index>` | Update job | Auth, CSRF, lost-update/version check |
| PATCH | `/api/jobs/<profile>/bulk` | Bulk update | Limits, atomicity, authorization |
| GET | `/api/jobs/<profile>/stats` | Job stats | Ownership and data minimization |
| POST | `/api/scrape/<profile>` | Start scrape | Auth, CSRF, concurrency and rate limits |
| GET | `/api/scrape/status` | Scrape status | Per-user job visibility |
| GET | `/api/form-config/<profile>` | Read form config | Redaction and ownership |
| PUT | `/api/form-config/<profile>` | Replace form config | Schema, CSRF, safe persistence |
| POST | `/api/form-config/<profile>/seed` | Seed config | Idempotency and ownership |
| GET | `/api/resumes/<profile>` | List resumes | Ownership and safe filenames |
| GET | `/api/resumes/<profile>/<filename>` | Download resume | Traversal, ownership, content headers |
| GET | `/api/ai-training/<profile>` | Read AI training state | Private-data boundary |
| PATCH | `/api/ai-training/<profile>/platforms/<platform_id>` | Update platform settings | Allow-list, CSRF, ownership |
| POST | `/api/ai-training/<profile>/generate-resume` | Generate resume | Cost/rate limits, input privacy, job lifecycle |
| GET | `/api/history/<profile>` | Read history | Ownership and retention |
| GET | `/api/setup` | Setup status | Redact paths/secrets in hosted response |
| GET | `/api/mode` | Deployment mode | Avoid leaking security assumptions |
| POST | `/api/profiles` | Create profile | Hosted code-execution boundary, validation |
| DELETE | `/api/profiles/<name>` | Delete profile | Re-auth/confirmation, CSRF, ownership |
| GET | `/api/profiles/<name>/search-strings` | Search suggestions | Ownership and bounded query |
| GET | `/api/profiles/<name>/roles` | List roles | Ownership |
| POST | `/api/profiles/<name>/roles` | Create role | Schema, CSRF, ownership |
| PUT | `/api/profiles/<name>/roles/<role_id>` | Update role | Schema, CSRF, ownership |
| DELETE | `/api/profiles/<name>/roles/<role_id>` | Delete role | CSRF, ownership, conflict semantics |
| POST | `/api/resumes/<profile>/upload` | Upload PDF | Size/MIME/magic/quota/ownership |
| DELETE | `/api/resumes/<profile>/<filename>` | Delete resume | Traversal, CSRF, ownership |
| GET | `/api/all-users` | List users | Admin-only; minimize metadata |

## Definition of audited

For each mutating route, add request/response schema, authentication, object authorization, CSRF decision, input/size limits, concurrency behavior, error codes, audit logging, and success/failure tests. Local-only routes must still validate paths and inputs.
