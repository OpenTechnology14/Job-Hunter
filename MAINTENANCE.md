# Job Hunter — Maintenance Guide

Reference for working on each part of the codebase. Read the relevant section before modifying.

---

## 1. Scrapers (`scraper.py`, `scraper_extended.py`, `scraper_web.py`)

### How they work
Each scraper function takes search queries + location and returns a list of job dicts. All use the `requests` library for HTTP calls. No authentication required for free sources.

### Standard job dict keys
```python
{
    "title": str,           # Job title
    "company": str,         # Company name
    "location": str,        # Location string
    "url": str,             # Application URL (used as dedup key)
    "salary": str,          # Salary range or empty
    "work_type": str,       # "Remote", "On-site", "Hybrid", or ""
    "source": str,          # Source name (e.g. "Greenhouse", "Himalayas")
    "apply_method": str,    # Optional: "Easy Apply", "Form Fill", etc.
}
```

### Adding a source
1. Write a `scrape_sourcename()` function returning list of job dicts
2. Add it to the scraper loop in `run_scrape.py`
3. Handle API errors gracefully - return empty list on failure, don't crash
4. Respect rate limits - add `time.sleep()` between paginated requests
5. Document in `SOURCES.md`

### Known issues
- Some APIs change their response format without notice. If a source returns 0 jobs unexpectedly, check the API response structure.
- Greenhouse and Lever require company slugs. Find these on company career pages.
- SerpAPI (Google Jobs) costs ~$100/mo. It's optional.

### Web search (`scraper_web.py`)
- DuckDuckGo HTML scraping (free, no API key) or Google via SerpAPI (paid)
- Company career pages: Greenhouse (30+ companies), Lever (18+), Workday (15+)
- Enabled by `web_search: True` in profile SEARCH_SETTINGS or `--web` flag
- Disabled with `--no-web` flag

### AI-training gigs (`ai_training.py`)
- Runs when the profile has a role with id exactly `ai-training` (skip with `--no-ai`)
- Two parts: a curated **platform directory** (15 signup-based marketplaces —
  DataAnnotation, Outlier, Alignerr, Mercor…) tracked per profile in
  `output/{profile}/ai_training.json`, and **scrapers** for real postings on
  Ashby/Greenhouse/Lever boards, title-filtered to trainer/annotator/rater roles
- Rows carry `role_hint="ai-training"` so the matcher force-assigns the category
- Add companies via `ASHBY_AI_COMPANIES` / `GREENHOUSE_AI_COMPANIES` / `LEVER_AI_COMPANIES`

### Freelance / part-time boards (`scraper_freelance.py`)
- Runs for any role with `"freelance_boards": True` (skip with `--no-freelance`)
- Freelancer.com public API (hour-capped when `max_hours_per_week` is set) plus
  one saved-search row per bot-blocked board (Upwork, PeoplePerHour, Guru, Braintrust)
- A loose relevance filter drops off-topic API hits (Freelancer's query match is broad)

### Boolean / X-Ray search (`boolean_query.py`)
- Runs for `"boolean_search": True` in SEARCH_SETTINGS (force `--xray`, skip `--no-xray`)
- `build_boolean(role_terms(...))` composes `("A" OR "B") AND (x OR y) NOT z` from
  `search_queries` (title OR-group) + optional `must_have` / `nice_to_have` + `exclude_keywords`
- `saved_search_rows()` → clickable LinkedIn/Indeed/Google-X-Ray rows (always; reliable)
- `run_xray_search()` → runs `site:boards.greenhouse.io ("A" OR "B")` etc. through
  `scraper_web`'s DuckDuckGo/SerpAPI engine and returns real ATS postings tagged with `role_hint`
- X-Ray queries are capped to `XRAY_MAX_TITLES` and drop exclusions — long whole-web
  queries return nothing; the matcher applies `exclude_keywords` downstream instead
- Free DuckDuckGo rate-limits (202 "challenge"); one retry, then a graceful 0 with a
  note that the clickable rows still work and `SERPAPI_KEY` makes the fetch reliable
- `search_strings()` is the no-network view the admin **Config** page renders per role
- **Add an ATS domain:** extend `XRAY_SITES` (must return individual postings via `site:`;
  Workday is intentionally excluded — its X-Ray hits are landing pages, not postings)

---

## 2. Matcher (`matcher.py`)

### How matching works
Two filters applied in sequence:

1. **Keyword match:** Job title must contain words from the role's `search_queries`. Case-insensitive. Partial word matching (e.g. "Engineer" matches "Software Engineer").

2. **Salary match:** If the job lists a salary, it must overlap with the role's `salary_min`/`salary_max` range. If no salary listed, the job passes through for manual review.

### Role assignment
Jobs are assigned to the first matching role profile. If no role matches, the job appears as "Unmatched - Review" in the spreadsheet.

### Hours cap (part-time roles)
- A role may set `"max_hours_per_week": N`. Title-matched jobs for that role
  must then show a part-time/contract/freelance signal in the title or
  description, or they're dropped (full-time postings can't fit the cap).
- Rows that arrive with a `role_hint` (freelance scrapers) bypass this — they
  were already filtered by stated weekly commitment upstream.

### Role assignment override
- A scraped row may carry `role_hint`; if it names a real role, the matcher
  assigns that role directly instead of keyword-matching the title.

### Tuning
- **Too few results:** Broaden `search_queries`, widen salary range
- **Too many irrelevant results:** Add terms to `exclude_keywords` in `SEARCH_SETTINGS`
- **Wrong category:** Reorder role profiles (first match wins)

---

## 2b. Quality Filters (`quality_filter.py`)

Post-match hygiene, applied in `run_scrape.py` right after `match_jobs()` and
toggleable per profile via `SEARCH_SETTINGS` (and the admin Config page):

- `filter_title_relevance` — title must contain a role keyword (with light stemming)
- `filter_usd_only` — drop non-USD budgets (foreign-client gigs)
- `filter_min_budget` — USD floor for freelance-project rows (0 = off)
- `filter_aggregators` — drop web-search "1,000+ jobs" listing pages
- Cross-source dedupe by normalized title+company (catches the same posting
  from two boards, which URL dedupe misses). `local_sync.push_jobs` applies the
  same title+company key against rows already in the CSV.

Saved-search rows (`🔎 …`) are always exempt. Retro-clean an existing sheet
with `python quality_filter.py --profile <p> --clean [--dry-run]` — approved
(`Y`/`Done`) rows are never touched.

---

## 3. Storage Layer (`storage.py`, `local_sync.py`, `sheets_sync.py`)

### Local CSV mode (default)
- `local_sync.py` reads/writes CSV files using Python's `csv` module
- Deduplication by URL: existing jobs are not overwritten
- New jobs are appended to the bottom
- Column order defined by `SHEET_COLUMNS` constant
- `cleanup_stale_jobs()` removes unapproved jobs older than `stale_days` (default 30, 0 = disabled)
  - Never removes jobs with Apply = "Y" or "Done"
  - Never removes jobs with no Date Found
  - Called automatically before each scrape (skip with `--no-cleanup`)

### Google Sheets mode (optional)
- `sheets_sync.py` uses `gspread` with a service account
- Same deduplication logic
- Requires: `GOOGLE_SHEET_ID` in profile, service account JSON in `credentials/`
- The `apps_script.js` file adds menu buttons to the Google Sheet

### Switching modes
Set `STORAGE_MODE` in the profile file. Both modes can coexist - they write to different targets.

---

## 4. Browser Automation (`browser_apply.py`)

### How auto-apply works
1. Reads CSV for jobs with Apply = "Y"
2. Opens Playwright Chromium in headed mode (visible to user)
3. For each job:
   - Navigates to URL
   - Detects form type (Easy Apply, file upload, form fill)
   - Fills standard fields from `USER_PROFILE`
   - Applies custom fields from `form_config.json`
   - Uploads resume PDF via `resume_picker.py`
   - **Pauses for user confirmation**
   - On confirm: submits, marks "Done" in CSV
4. `--dry-run` flag: does everything except submit

### Form detection
The automation looks for common form patterns:
- File input elements (resume upload)
- Text inputs with labels matching known fields (name, email, phone)
- Select dropdowns matched against `select_defaults` patterns
- EEO/self-ID comboboxes (rendered as `<input>` on Greenhouse) — matched
  against the same `select_defaults` rules as a fallback on text inputs
- Submit/Apply buttons

### Auto-fill field catalog (`ats_fields.py`)
- `form_config.json` is seeded from a catalog of the real fields on
  Greenhouse, Lever, Workday, Ashby, iCIMS, Indeed, and LinkedIn forms
- `seed_form_config()` merges missing rules in without overwriting edited
  values; `--reset` rebuilds from scratch. New profiles seed automatically;
  the admin Form Fill page has a **Seed from job-board catalog** button
- Dropdown answers use `a|b|c` candidate lists (per-ATS wording differs);
  `browser_apply` tries each in order via `select_option`, and as typed text
  on comboboxes

### Screener-question guard (data-leak protection)
- Built-in identity patterns (`FIELD_PATTERNS`) are matched with unanchored
  `re.search` against the whole label, so a long question like "…require
  sponsorship at your current location?" could substring-match `location`
  and dump the city value into it.
- `_is_screener_question()` classifies a field as a free-text question ("?" or
  >7 words) and skips the identity autofill for it — only the explicit,
  intentional `custom_fields` rules apply. City/state/country patterns are also
  word-bounded so "relocation" can't match.
- This was found and fixed by a live dry-run pass against a real Greenhouse
  form; see TESTING.md → "Auto-fill against a live form".

### What it can't handle
- CAPTCHAs
- Multi-page applications with complex state
- Sites that require login (LinkedIn, Indeed)
- Heavy JavaScript SPAs that resist automation

---

## 5. Profile System (`config.py`, `profiles/`)

### Profile structure
Each profile is a Python file with these top-level variables:
- `USER_PROFILE` - dict with name, email, phone, skills, etc.
- `ROLE_PROFILES` - dict of role categories with search queries + salary + resume file
- `SEARCH_SETTINGS` - locations, exclude keywords, max results, `web_search` (bool), `stale_days` (int)
- `LOCATION_FILTER` - city, state, radius, nearby_cities, include_remote
- `STORAGE_MODE` - "local" or "google"
- `INTERESTING_ROLE` - fallback role for unmatched-but-interesting jobs

### Loading
`config.py` uses `importlib` to load profile modules by name. The `--profile` CLI argument maps to a filename in `profiles/`.

### Security note
Profile files are executed as Python code. Never load untrusted profile files. In deployed mode, the admin panel creates profiles from a safe template.

---

## 6. Admin Panel (`admin/`)

### Architecture
- Flask server on port 5175, binds to `127.0.0.1`
- No build step - single HTML file with inline CSS/JS
- Reads/writes project files directly (CSV, JSON, Python profiles)
- Scrape buttons spawn `run_scrape.py` as subprocess in background thread
- No database - filesystem is the database
- No authentication - localhost only

### Two modes
- **Local** (default): Profile dropdown, single-user view
- **Deployed** (`--deployed` or `DEPLOYED=1`): Multi-user with expandable sections, profile creation, resume upload/delete

### API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/mode` | Returns `{deployed: bool}` |
| GET | `/api/profiles` | List all profiles with job/resume counts |
| GET | `/api/profiles/<name>` | Profile config (user info, roles, etc.) |
| POST | `/api/profiles` | Create new profile from template |
| DELETE | `/api/profiles/<name>` | Delete profile file (keeps output data) |
| GET | `/api/jobs/<profile>?source=api\|browser` | List jobs with filters |
| PATCH | `/api/jobs/<profile>/<index>` | Update single job field |
| PATCH | `/api/jobs/<profile>/bulk` | Bulk update jobs |
| GET | `/api/jobs/<profile>/stats` | Job statistics by category/source |
| POST | `/api/scrape/<profile>` | Start scrape (api/browser/both) |
| GET | `/api/scrape/status` | Check running scrapes |
| GET | `/api/form-config/<profile>` | Get form auto-fill config |
| PUT | `/api/form-config/<profile>` | Update form auto-fill config |
| GET | `/api/resumes/<profile>` | List resume PDFs |
| GET | `/api/resumes/<profile>/<filename>` | Serve resume PDF |
| POST | `/api/resumes/<profile>/upload` | Upload resume PDF |
| DELETE | `/api/resumes/<profile>/<filename>` | Delete resume PDF |
| GET | `/api/history/<profile>` | Run history (last 50) |
| GET | `/api/setup` | System setup check |
| GET | `/api/all-users` | All profiles summary (deployed mode) |

---

## 7. Resume System (`resume_picker.py`, `generate_resumes.py`)

### Resume picker
Maps job's matched role category to the corresponding `resume_file` from `ROLE_PROFILES`. Returns the full path to the PDF in `output/{profile}/resumes/`.

### Resume generator
`generate_resumes.py` generates resume PDFs using `fpdf2` (Helvetica font, no Unicode). Produces 2-page resumes with:
- Header block (name, contact info)
- Summary paragraph
- Work experience with bullets
- Skills section
- Education

### Adding resumes manually
Drop PDF files in `output/{profile}/resumes/` with filenames matching the `resume_file` values in the profile's `ROLE_PROFILES`.

---

## 8. Dependencies

```
requests        - HTTP client for API scrapers
playwright      - Browser automation for scraping + auto-apply
python-dotenv   - .env file loading
fpdf2           - PDF resume generation
flask           - Admin panel API server
```

Optional (Google Sheets mode):
```
gspread         - Google Sheets API client
google-auth     - Google service account auth
gspread-formatting - Sheet formatting
```
