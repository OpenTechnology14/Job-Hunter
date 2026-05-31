# Job Hunter — App Playbook

Single-source reference for the entire codebase. Read the relevant section before modifying any part of the system.

---

## System Overview

Job Hunter is a local-first job hunting automation tool. It scrapes free job board APIs, filters results by keyword and salary, stores them in a spreadsheet, and optionally auto-applies via browser automation. No AI, no cloud services required for core functionality.

**Stack:** Python 3.8+, requests, Playwright, Flask, fpdf2
**Data store:** filesystem (CSV, JSON, Python profile files)
**Deployment:** local machine or server with `--deployed` flag

---

## Entry Points

| Command | File | Purpose |
|---------|------|---------|
| `python run_scrape.py --profile name` | `run_scrape.py` | API + web scraping (Phase 1A) |
| `python run_scrape.py --profile name --no-web` | `run_scrape.py` | API only, skip web search |
| `python run_scrape.py --profile name --no-cleanup` | `run_scrape.py` | Skip stale job removal |
| `python run_tests.py [--all\|--api\|--browser] [-v]` | `run_tests.py` | Automated test runner |
| `python run_scrape_browsers.py --profile name` | `run_scrape_browsers.py` | LinkedIn/Indeed scraping (Phase 1B) |
| `python run_apply.py --profile name [--dry-run]` | `run_apply.py` | Browser auto-apply (Phase 2) |
| `python admin/server.py [--deployed]` | `admin/server.py` | Web admin panel |
| `python generate_resumes.py --profile name` | `generate_resumes.py` | PDF resume generation |
| `python resume_picker.py --profile name` | `resume_picker.py` | Verify resume mapping |

---

## Data Flow

```
1. Profile loaded (config.py reads profiles/name.py)
2. Search queries + location extracted from ROLE_PROFILES + SEARCH_SETTINGS
3. Stale unapproved jobs cleaned up (if stale_days > 0)
4. Scrapers hit job board APIs (scraper.py, scraper_extended.py)
5. Web search runs (scraper_web.py — DuckDuckGo + company career pages)
6. Raw jobs filtered by matcher.py (keyword match + salary range overlap)
7. Matched jobs written to CSV or Google Sheet (storage.py -> local_sync.py | sheets_sync.py)
6. User reviews spreadsheet, marks Apply = "Y"
7. Auto-apply reads Y jobs, opens Playwright browser (browser_apply.py)
8. resume_picker.py selects correct PDF per role category
9. Browser fills forms, uploads resume, pauses before submit
10. On confirm: submits, marks "Done" in CSV
```

---

## Module Reference

### config.py — Profile Loader
- Uses `importlib` to load profile `.py` files by name
- `--profile` CLI argument maps to filename in `profiles/`
- Exports: `USER_PROFILE`, `ROLE_PROFILES`, `SEARCH_SETTINGS`, `LOCATION_FILTER`, `STORAGE_MODE`
- **Security:** profiles are executed as Python code. Never load untrusted files.

### scraper.py — Core API Scrapers
6 scrapers, all using `requests`. No auth required for free sources.
- `scrape_greenhouse(queries, location, company_slugs)`
- `scrape_lever(queries, location, company_slugs)`
- `scrape_himalayas(queries, location, max_results)`
- `scrape_remoteok(queries, location, max_results)`
- `scrape_usajobs(queries, location, max_results)` — needs API key
- `scrape_arbeitnow(queries, location, max_results)`

### scraper_extended.py — Extended Scrapers
11 additional scrapers. Some require API keys, some use browser automation.
- Workday, The Muse, Wellfound, Adzuna, Google Jobs (SerpAPI)
- Browser-based: LinkedIn, Indeed

### scraper_web.py — Internet-Wide Search
Searches beyond job boards using two strategies:
- **Search engines:** DuckDuckGo HTML scraping (free) or Google via SerpAPI (paid)
- **Company career pages:** Greenhouse (30+ companies), Lever (18+), Workday (15+)
- Entry point: `scrape_web_sources(queries, location, max_results)`
- Automatically enabled when `web_search: True` in profile SEARCH_SETTINGS

### matcher.py — Job Matching
Two sequential filters:
1. **Keyword match:** title must contain words from role's `search_queries` (case-insensitive, partial)
2. **Salary match:** if salary listed, must overlap role's `salary_min`/`salary_max` range. No salary = passes through.

Jobs assigned to first matching role. Unmatched jobs appear as "Unmatched - Review."

### storage.py — Storage Router
Checks `STORAGE_MODE` and delegates to `local_sync` or `sheets_sync`.

### local_sync.py — CSV Backend
- Reads/writes CSV using Python's `csv` module
- Deduplication by URL (existing jobs not overwritten)
- New jobs appended to bottom
- Column order defined by `SHEET_COLUMNS`
- `cleanup_stale_jobs()` — removes unapproved jobs older than `stale_days` (never touches Y/Done)

### sheets_sync.py — Google Sheets Backend
- Uses `gspread` with service account
- Same dedup logic as local
- Requires `GOOGLE_SHEET_ID` + service account JSON in `credentials/`

### browser_apply.py — Auto-Apply
1. Reads CSV for jobs with Apply = "Y"
2. Opens Playwright Chromium in headed mode
3. Per job: navigate, detect form type, fill fields from `USER_PROFILE`, upload resume, pause for confirmation
4. `--dry-run`: everything except submit

Form detection patterns: file inputs, text inputs with known labels, select dropdowns, submit buttons.

**Cannot handle:** CAPTCHAs, multi-page apps, login-required sites, heavy JS SPAs.

### resume_picker.py — Resume Selection
Maps job's matched role category to `resume_file` from `ROLE_PROFILES`. Returns full path to PDF in `output/{profile}/resumes/`.

### generate_resumes.py — PDF Generator
Uses `fpdf2` with Helvetica font. Produces 2-page resumes: header, summary, experience, skills, education.

---

## Profile System

### Profile Variables

| Variable | Type | Purpose |
|----------|------|---------|
| `USER_PROFILE` | dict | name, email, phone, city, skills, work history |
| `ROLE_PROFILES` | dict | role categories with search queries, salary range, resume file |
| `SEARCH_SETTINGS` | dict | locations, exclude keywords, max results, `web_search` (bool), `stale_days` (int) |
| `LOCATION_FILTER` | dict | city, state, radius, nearby_cities, include_remote |
| `STORAGE_MODE` | str | `"local"` or `"google"` |
| `INTERESTING_ROLE` | str | fallback role for unmatched-but-interesting jobs |

### Standard Job Dict Keys

Every scraper returns dicts with these keys:

```python
{
    "title": str,
    "company": str,
    "location": str,
    "url": str,           # dedup key
    "salary": str,
    "work_type": str,     # "Remote", "On-site", "Hybrid", ""
    "source": str,
    "apply_method": str,  # optional
}
```

### CSV Columns

`SHEET_COLUMNS`: Job Title, Company, Location, Work Type, Salary, Role Category, Match Reason, Apply Method, Apply, Resume Version, URL, Source, Date Found, Date Applied, Notes

`BROWSER_COLUMNS`: adds Easy Apply, Direct Apply Link

---

## Admin Panel

### Server: `admin/server.py`
- Flask on port 5175, binds to `127.0.0.1`
- No build step, no database, no authentication
- Reads/writes project files directly
- Scrape buttons spawn `run_scrape.py` as subprocess

### Two Modes

| Mode | Flag | Behavior |
|------|------|----------|
| Local (default) | none | Profile dropdown, single-user view |
| Deployed | `--deployed` or `DEPLOYED=1` | Multi-user expandable sections, profile creation, resume upload/delete |

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/mode` | Returns `{deployed: bool}` |
| GET | `/api/profiles` | List profiles with job/resume counts |
| GET | `/api/profiles/<name>` | Profile config |
| POST | `/api/profiles` | Create profile from template |
| DELETE | `/api/profiles/<name>` | Delete profile file |
| GET | `/api/jobs/<profile>` | List jobs with filters |
| PATCH | `/api/jobs/<profile>/<index>` | Update single job field |
| PATCH | `/api/jobs/<profile>/bulk` | Bulk update jobs |
| GET | `/api/jobs/<profile>/stats` | Job statistics |
| POST | `/api/scrape/<profile>` | Start scrape |
| GET | `/api/scrape/status` | Check running scrapes |
| GET/PUT | `/api/form-config/<profile>` | Form auto-fill config |
| GET | `/api/resumes/<profile>` | List resume PDFs |
| GET | `/api/resumes/<profile>/<file>` | Serve resume PDF |
| POST | `/api/resumes/<profile>/upload` | Upload resume PDF |
| DELETE | `/api/resumes/<profile>/<file>` | Delete resume PDF |
| GET | `/api/history/<profile>` | Run history |
| GET | `/api/setup` | System setup check |
| GET | `/api/all-users` | All profiles summary (deployed) |

### Dashboard Pages
1. **Dashboard** — job counts, category breakdown, scrape buttons
2. **Jobs** — table with approve/reject, search, filters
3. **Config** — profile info, location, roles
4. **Form Fill** — form_config.json editor
5. **Resumes** — PDF cards with view/upload/delete
6. **History** — scrape/apply run log
7. **Setup** — system health check

---

## Dependencies

### Core (required)
```
requests         — HTTP client for API scrapers
playwright       — Browser automation
python-dotenv    — .env file loading
fpdf2            — PDF resume generation
flask            — Admin panel server
```

### Optional (Google Sheets mode)
```
gspread              — Google Sheets API client
google-auth          — Service account auth
gspread-formatting   — Sheet formatting
```

---

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `USAJOBS_API_KEY` | No | USAJobs API access |
| `USAJOBS_EMAIL` | No | Required with USAJobs key |
| `SERPAPI_KEY` | No | Google Jobs via SerpAPI |
| `ADZUNA_APP_ID` | No | Adzuna API access |
| `ADZUNA_APP_KEY` | No | Adzuna API access |
| `GOOGLE_SHEET_ID` | No | Google Sheets target |
| `DEPLOYED` | No | Set `1` for multi-user admin mode |

---

## Security Considerations

1. **Admin panel has no auth.** Localhost only. Add auth before exposing publicly.
2. **Profile loading uses `exec()`.** Only load trusted profile files.
3. **Server binds to `127.0.0.1`.** Do not change to `0.0.0.0` without auth.
4. **`.env` is gitignored.** API keys never committed.
5. **CSV contains personal info** from profile config (name, email, phone).
6. **Profile `.py` files are gitignored** (except example and __init__).

---

## Adding a Job Board Source

1. Write `scrape_sourcename(queries, location, max_results)` in `scraper.py` or `scraper_extended.py`
2. Return list of job dicts with standard keys
3. Handle API errors gracefully — return empty list on failure
4. Add `time.sleep()` between paginated requests
5. Call it from `run_scrape.py` scraper loop
6. Document in `SOURCES.md`
7. Test: `python run_scrape.py --profile yourname`

---

## Tuning Match Results

| Problem | Fix |
|---------|-----|
| Too few results | Broaden `search_queries`, widen salary range |
| Too many irrelevant | Add terms to `exclude_keywords` in `SEARCH_SETTINGS` |
| Wrong category | Reorder role profiles (first match wins) |
| Missing salary jobs | They pass through by default for manual review |

---

## File Output Structure

```
output/{profile}/
|-- jobs.csv              # API scrape results, main apply list
|-- browser_jobs.csv      # LinkedIn/Indeed results (manual apply)
|-- form_config.json      # Custom form field mappings
|-- run_log.json          # Scrape/apply run history
|-- data/
|   |-- scraped_jobs.json # Raw scraper output
|   +-- matched_jobs.json # Post-matcher output
+-- resumes/
    |-- software_engineer.pdf
    |-- product_manager.pdf
    +-- data_analyst.pdf
```
