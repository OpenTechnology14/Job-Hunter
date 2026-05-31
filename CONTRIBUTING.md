# Contributing to Job Hunter

---

## Architecture

```
job-hunter/
|
|-- run_scrape.py            Entry point: API scraping (Phase 1A)
|-- run_scrape_browsers.py   Entry point: LinkedIn/Indeed scraping (Phase 1B)
|-- run_apply.py             Entry point: auto-apply (Phase 2)
|
|-- config.py                Profile loader (importlib) + LOCATION_FILTER
|-- storage.py               Routes to local_sync or sheets_sync
|-- local_sync.py            CSV backend (default)
|-- sheets_sync.py           Google Sheets backend (optional)
|
|-- scraper.py               API scrapers: Greenhouse, Lever, Himalayas,
|                            RemoteOK, USAJobs, Arbeitnow
|-- scraper_extended.py      Extended scrapers: Workday, The Muse, Wellfound,
|                            Adzuna, Google Jobs (SerpAPI)
|-- matcher.py               Keyword + salary matching (no AI)
|-- resume_picker.py         Maps role category -> resume PDF
|-- browser_apply.py         Playwright browser automation for form fill
|-- generate_resumes.py      PDF resume generator (fpdf2)
|
|-- admin/
|   |-- server.py            Flask API server (port 5175, localhost)
|   +-- static/index.html    Single-page admin dashboard
|
|-- profiles/
|   |-- example_profile.py   Template - copy for each person
|   +-- __init__.py
|
|-- output/{profile}/
|   |-- jobs.csv             API job results (auto-apply eligible)
|   |-- browser_jobs.csv     LinkedIn/Indeed results (manual apply)
|   |-- form_config.json     Form auto-fill field mappings
|   |-- run_log.json         Scrape/apply run history
|   |-- data/                Scraped/matched JSON intermediates
|   +-- resumes/             User's resume PDFs
|
|-- docs/
|   |-- ADMIN_PANEL.md       Admin panel build spec
|   +-- USER_GUIDE.md        Non-technical user guide
|
|-- .env.example             Environment variable template
|-- requirements.txt         Python dependencies
+-- form_config_example.json Template for form auto-fill config
```

---

## Data Flow

```
Profile (.py)
    |
    v
Scraper (scraper.py / scraper_extended.py)
    | hits job board APIs with search queries from profile
    v
Matcher (matcher.py)
    | filters by keyword match + salary range overlap
    v
Storage (local_sync.py or sheets_sync.py)
    | writes to CSV or Google Sheet
    v
User reviews spreadsheet, marks jobs Y/N
    |
    v
Auto-Apply (browser_apply.py)
    | reads Y jobs, opens Playwright browser
    | resume_picker.py selects correct PDF per role
    | fills forms, uploads resume, pauses before submit
    v
Job marked "Done" in spreadsheet
```

---

## Key Design Decisions

1. **No AI required.** Matching is keyword + salary range. No LLM calls, no API keys for core functionality.
2. **Filesystem is the database.** CSV files, JSON configs, Python profile files. No database server.
3. **Profile isolation.** Each person's data is fully isolated in `output/{name}/`. No cross-contamination.
4. **Visible browser automation.** Playwright runs in headed mode so the user can watch and intervene. Always pauses before submit.
5. **Two storage backends.** Local CSV (zero setup) or Google Sheets (cloud access). Set per profile.
6. **Admin panel is optional.** Everything works via CLI. The admin panel is a convenience layer.

---

## File Responsibilities

### Entry Points

| File | Purpose |
|------|---------|
| `run_scrape.py` | CLI entry for API scraping. Loads profile, runs scrapers, matches, saves to CSV/Sheet. |
| `run_scrape_browsers.py` | CLI entry for LinkedIn/Indeed browser scraping. Saves to `browser_jobs.csv`. |
| `run_apply.py` | CLI entry for auto-apply. Reads CSV for Y jobs, runs browser automation. |

### Core Modules

| File | Purpose |
|------|---------|
| `config.py` | Loads profile by name via `importlib`. Exports `USER_PROFILE`, `ROLE_PROFILES`, `SEARCH_SETTINGS`, `LOCATION_FILTER`. |
| `scraper.py` | 6 API scrapers. Each returns list of job dicts with standard keys. |
| `scraper_extended.py` | 11 additional scrapers (Workday, Muse, Wellfound, Adzuna, Google Jobs, browser-based sources). |
| `matcher.py` | `match_jobs(jobs, role_profiles, location_filter)` - filters by keyword overlap and salary range. |
| `resume_picker.py` | `pick_resume(job, role_profiles)` - returns PDF path based on matched role category. |
| `browser_apply.py` | Playwright automation: navigate to job URL, detect form type, fill fields, upload resume, pause before submit. |
| `storage.py` | Router: checks `STORAGE_MODE` and delegates to `local_sync` or `sheets_sync`. |
| `local_sync.py` | Read/write CSV files with deduplication by URL. |
| `sheets_sync.py` | Read/write Google Sheets via `gspread`. |

### Admin Panel

| File | Purpose |
|------|---------|
| `admin/server.py` | Flask API. Reads/writes project files directly. Spawns scrape subprocesses. Two modes: local (single user) and deployed (multi-user with expandable sections). |
| `admin/static/index.html` | Single-page app. 7 pages: Dashboard, Jobs, Config, Form Fill, Resumes, History, Setup. Dark theme, no build step. |

---

## Adding a New Job Board Source

1. Add a scraper function in `scraper.py` or `scraper_extended.py`:
   ```python
   def scrape_newboard(queries, location, max_results=25):
       """Returns list of job dicts."""
       jobs = []
       for query in queries:
           # Hit API, parse response
           jobs.append({
               "title": "...",
               "company": "...",
               "location": "...",
               "url": "...",
               "salary": "...",
               "work_type": "Remote",  # or "On-site", "Hybrid"
               "source": "NewBoard",
           })
       return jobs
   ```

2. Call it from `run_scrape.py` in the scraper loop.

3. Add it to `SOURCES.md` with auth requirements and coverage notes.

4. Test: `python run_scrape.py --profile yourname` and check the CSV for new results.

---

## Adding a Custom Field to Form Auto-Fill

Edit `output/{profile}/form_config.json`:

```json
{
  "custom_fields": [
    {"pattern": "regex_matching_field_label", "value": "auto-fill value"}
  ],
  "select_defaults": [
    {"pattern": "regex_matching_dropdown_label", "value": "option text"}
  ]
}
```

The `pattern` is matched case-insensitively against form field labels during auto-apply.

---

## Conventions

- **No inline secrets.** All API keys go in `.env`. Personal info goes in profile files (gitignored).
- **Standard job dict keys.** Every scraper returns: `title`, `company`, `location`, `url`, `salary`, `work_type`, `source`. Optional: `apply_method`, `easy_apply`, `direct_apply_link`.
- **CSV column order matters.** `SHEET_COLUMNS` and `BROWSER_COLUMNS` in `admin/server.py` define the canonical column order. Don't reorder without updating both.
- **Profile files are Python.** They're loaded with `exec()` / `importlib`. Keep them as pure data (dicts and lists). No imports, no side effects.
- **Admin panel has no build step.** It's a single HTML file with inline CSS/JS. Keep it that way.

---

## Running Tests

No automated test suite yet. Manual testing:

```bash
# Verify profile loads
python resume_picker.py --profile yourname

# Dry run scrape (check output)
python run_scrape.py --profile yourname

# Dry run apply (browser opens but doesn't submit)
python run_apply.py --profile yourname --dry-run

# Admin panel
python admin/server.py
# Open http://localhost:5175
```

---

## Environment Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp profiles/example_profile.py profiles/yourname.py
# Edit profile, add resumes to output/yourname/resumes/
```
