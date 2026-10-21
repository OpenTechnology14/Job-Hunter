---
name: code-creation
description: Rules for adding or changing Job-Hunter code — module boundaries, the standard job dict, profile/storage conventions, the supervision invariant, and test discipline with run_tests.py.
when_to_use: Use when writing a new feature, scraper/source, matcher or quality-filter rule, admin route/page, browser-apply behavior, or any bug fix in this repo. Triggers - "add a source", "new scraper", "add a flag", "fix bug", "add admin endpoint", "change matching", "auto-fill", "write tests".
---

# Code creation — Job-Hunter

Sources: `AGENTS.md`, `CONTRIBUTING.md`, `MAINTENANCE.md`, `APP_PLAYBOOK.md`,
`CLAUDE.md`, `TESTING.md`, `docs/IMPLEMENTATION_NOTES.md`,
`docs/proposals/PROPOSAL_RELEASE_AND_SAFETY_GAP_CLOSURE.md`. If this skill and
those files disagree, the files win — fix this skill.

## Stack (what actually exists)

- Python, flat module layout at repo root. No package, no `setup.py`/`pyproject.toml`.
  Python floor is documented inconsistently (`APP_PLAYBOOK.md` says 3.8+,
  `CLAUDE.md` says 3.10+) — don't use syntax newer than 3.10.
- `requests` (scrapers), `playwright` (browser scrape + apply), `flask`
  (admin panel), `fpdf2` (resumes), `python-dotenv`. Optional: `gspread`,
  `google-auth`, `gspread-formatting`. See `requirements.txt`.
- **No linter/formatter config and no CI workflow in the repo.** Match the
  surrounding file's style; don't introduce a new tool in a feature PR.
- Admin panel: `admin/server.py` + a single `admin/static/index.html` with
  inline CSS/JS. **No build step — keep it that way.**

## Non-negotiables (from `AGENTS.md` — never trade these for a feature)

1. Nothing submits an application without a fresh, explicit user confirmation
   for that exact job/page state. Dry-run must be structurally unable to call
   a submit primitive.
2. Profiles, resumes, form answers, credentials, browser sessions, history stay
   local unless a documented, field-level integration is explicitly enabled.
3. Profile `.py` files are trusted executable code. Never accept them from
   untrusted/hosted users.
4. Don't present the Flask admin server as hosted/multi-user ready.
5. "No AI" in the product: matching/filtering is deterministic; no LLM calls,
   no AI API keys in core functionality.

## Where code goes

| Change | Location | Also update |
|---|---|---|
| New job source | `scraper.py` / `scraper_extended.py` (or a themed module like `scraper_freelance.py`, `ai_training.py`) | call site in `run_scrape.py`; `SOURCES.md`; README sources table |
| Matching rule | `matcher.py` | `MAINTENANCE.md` §2 |
| Post-match hygiene | `quality_filter.py` (toggle via `SEARCH_SETTINGS`) | admin Config toggle; `MAINTENANCE.md` §2b |
| Storage | `local_sync.py` and `sheets_sync.py` together (routing in `storage.py`) | |
| Form auto-fill rules | `ats_fields.py` catalog / `form_config.json` | never weaken `_is_screener_question()` |
| Admin route | `admin/server.py` | `MAINTENANCE.md` §6 table, `docs/API_ROUTE_AUDIT_LEDGER.md` |
| New profile key | `profiles/example_profile.py` (placeholders only) + `config.py` default via `getattr` | `CLAUDE.md` setup steps |
| New CLI flag | the `run_*.py` entry point | README, `CLAUDE.md` flags list, `TESTING.md` scenario |

## Conventions

- **Standard job dict:** every scraper returns `title, company, location, url,
  salary, work_type, source`; optional `apply_method, easy_apply,
  direct_apply_link, role_hint`. `url` is the dedupe key.
- **Scrapers fail soft:** return `[]` on error, never crash the run; `time.sleep()`
  between paginated requests; respect site terms (no LinkedIn/Indeed account
  automation — `FUTURE.md` "Won't Do").
- **Column order is canonical:** `SHEET_COLUMNS` / `BROWSER_COLUMNS` in
  `admin/server.py`. Don't reorder without updating both and the docs.
- **Profiles are pure data** (dicts/lists, no imports, no side effects). New
  settings get a safe default in `config.py` so old profiles keep working.
- **Filesystem is the database.** No DB server. Paths touched by background
  scraping *and* UI mutation need atomic/concurrency-safe writes (open gap JH-010).
- **Validate at trust boundaries:** profile names, filenames, URLs, uploads,
  external payloads.
- **Secrets** in `.env` only; examples use placeholders. Never commit real
  names, emails, phones, cities, or resumes — the public `main` was scrubbed
  of these once already.

## Test discipline

Current runner (verified): `python run_tests.py` with category flags
`--api --browser --matcher --storage --all -v`. It's a custom runner, not
pytest. Some categories make live HTTP calls.

Rules (from `AGENTS.md` / `docs/CONTINUOUS_IMPROVEMENT.md`):

- Every bug fix ships a regression test; every escaped defect becomes a fixture.
- Tests call the exported production function — don't re-implement logic in
  the test (open gap JH-014).
- Synthetic identities + temporary directories only. Never import or print the
  operator's active profile; never write into real `output/` (open gap JH-002).
- Deterministic tests are the gate; live provider checks are smoke tests and
  must not be the only evidence. Provider downtime never justifies weakening
  a deterministic gate.
- Browser safety changes need a test proving dry-run makes **zero** submit calls.

*Proposed, not built:* migration to `python -m pytest -m "not live and not
browser_live"` as the default offline command, plus a CI workflow (JH-001,
JH-005). Don't claim either exists until it lands.

## Before you call it done

1. `python run_tests.py` (or the relevant `--category`) — report actual output.
2. For browser-apply changes: a `--dry-run` pass, observed.
3. Docs updated per the table above (see the `docs` skill).
4. PR template checklist (`.github/PULL_REQUEST_TEMPLATE.md`) filled honestly.
