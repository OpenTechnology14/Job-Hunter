# CLAUDE.md — Job Hunter Automation System

## Project Overview

A two-phase local job hunting automation system. No cloud hosting, no AI API
keys required.

**Phase 1 — Scrape:** Python scripts hit free job board APIs, match jobs by
keyword and salary range, and push results to a local CSV file or Google Sheet.

**Phase 2 — Apply:** After the user reviews the spreadsheet and marks jobs as
"✅ Ready to Apply," a separate script reads those rows, opens a Playwright
browser, picks the right resume PDF per role type, and fills/submits applications.
Always supervised (browser visible, pauses before submit). Has a --dry-run mode.

**Two storage modes:**
- **Local (default):** CSV file at `output/{profile}/jobs.csv` — open in
  Excel, Numbers, LibreOffice. Zero setup. No Google account needed.
- **Google Sheets:** Requires a service account (one-time setup). Adds
  in-sheet menu buttons and cloud access from any device.

Set `STORAGE_MODE = "local"` or `"google"` in the profile file.

---

## Project Structure

```
job-hunter/
├── CLAUDE.md                ← This file
├── SOURCES.md               ← All 17 job board sources + setup guide
├── config.py                ← Profile loader + LOCATION_FILTER
├── storage.py               ← Routes to local_sync or sheets_sync
├── local_sync.py            ← Local CSV backend (default)
├── sheets_sync.py           ← Google Sheets backend (optional)
├── profiles/
│   ├── example_profile.py   ← Template — copy for each person
│   ├── alex.py              ← Alex's profile
│   └── marcelli.py          ← Marcelli's profile
├── scraper.py               ← API scrapers (sources 1-6)
├── scraper_extended.py      ← Extended scrapers (sources 7-17)
├── scraper_web.py           ← Internet-wide search (DuckDuckGo + career pages)
├── ai_training.py           ← AI-training module: platform directory + scrapers (sources 18-20)
├── scraper_freelance.py     ← Freelance boards: Freelancer.com API + saved part-time searches (source 21)
├── boolean_query.py         ← Boolean string builder + Google X-Ray over ATS boards (opt-in)
├── matcher.py               ← Keyword + salary matching (no AI)
├── quality_filter.py        ← Result hygiene: relevance, USD/budget, aggregator pages, dedupe
├── ats_fields.py            ← Auto-fill field catalog from real ATS forms (Greenhouse/Lever/Workday/...)
├── browser_apply.py         ← Playwright browser automation
├── resume_picker.py         ← Maps role → resume PDF
├── run_scrape.py            ← Phase 1A: API scrape → jobs.csv (+ web search + stale cleanup)
├── run_scrape_browsers.py   ← Phase 1B: LinkedIn+Indeed → browser_jobs.csv
├── run_tests.py             ← Automated test runner (API, matcher, storage, browser)
├── run_apply.py             ← Phase 2: auto-apply (jobs.csv only)
├── generate_resumes.py      ← PDF resume generator (fpdf2)
├── form_config_example.json ← Template for form auto-fill config
├── apps_script.js           ← Google Apps Script for sheet menu buttons
├── admin/                   ← Admin Panel UI (localhost)
│   ├── server.py            ← Flask API server (port 5175)
│   └── static/
│       └── index.html       ← Single-page admin dashboard
├── docs/
│   ├── ADMIN_PANEL.md       ← Full admin panel build spec
│   └── USER_GUIDE.md        ← Non-technical user guide
├── requirements.txt
├── .env.example
├── credentials/             ← Google service account JSON (user creates)
└── output/
    └── {profile}/
        ├── jobs.csv         ← Main job list (API sources, auto-apply eligible)
        ├── browser_jobs.csv ← LinkedIn/Indeed (informational, no auto-apply)
        ├── form_config.json ← Form auto-fill field mappings
        ├── run_log.json     ← Scrape/apply run history
        ├── data/            ← Scraped/matched JSON files
        └── resumes/         ← User's resume PDFs
```

## Multi-Profile System

Each person gets: 1 profile file + 1 spreadsheet (local CSV or Google Sheet) + 1 resume PDF per role.
Everything is selected by `--profile`:

```bash
python run_scrape.py --profile alex
python run_apply.py --profile jane --dry-run
```

---

## SETUP GUIDE — Walk the user through these steps

### Part 1: Python Environment (one-time)

**Step 1:** Verify Python 3.10+ is installed:
```bash
python3 --version
```
If not installed: Mac `brew install python3`, Windows download from python.org.

**Step 2:** Navigate to the project folder:
```bash
cd job-hunter
```

**Step 3:** Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

**Step 4:** Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

### Part 2: Set Up a Person (repeat per person)

**Step 5:** Create their profile:
```bash
cp profiles/example_profile.py profiles/theirname.py
```

**Step 6:** Edit the profile file — fill in:
- `USER_PROFILE` — name, email, phone, skills
- `ROLE_PROFILES` — add as many roles as needed, each with:
  - `search_queries` — job titles to search for
  - `salary_min` / `salary_max` — target range
  - `resume_file` — PDF filename
- `SEARCH_SETTINGS` — locations, filters, plus:
  - `web_search: True` — search DuckDuckGo + company career pages (enabled by default)
  - `stale_days: 30` — auto-remove unapproved jobs older than N days (0 = disabled)
- `STORAGE_MODE` — "local" (default) or "google"

**Step 7:** Create a resume PDF per role and drop them in:
```bash
mkdir -p output/theirname/resumes
# Copy or move PDF files there (one per role in ROLE_PROFILES)
```

**Step 8:** Verify resume setup:
```bash
python resume_picker.py --profile theirname
```

**Step 9:** Run the first scrape:
```bash
python run_scrape.py --profile theirname
```

For local mode, this creates `output/theirname/jobs.csv`. Open it in
Excel, Numbers, or LibreOffice. Change the Status column to
"✅ Ready to Apply" for jobs you want, save the file, then run Phase 2.

### Part 3: Google Sheets Setup (OPTIONAL — only if STORAGE_MODE = "google")

Skip this entire section if using local CSV mode.

**Step 10:** Go to https://console.cloud.google.com

**Step 11:** Create a new project called "Job Hunter"

**Step 12:** Enable APIs — go to APIs & Services → Library:
- Search "Google Sheets API" → Enable
- Search "Google Drive API" → Enable

**Step 13:** Create credentials — go to APIs & Services → Credentials:
- Create Credentials → Service Account
- Name: "job-hunter-bot"
- Role: Editor
- Go to Keys tab → Add Key → Create New Key → JSON → Create
- A .json file downloads

**Step 14:** Save the credentials:
```bash
mkdir -p credentials
mv ~/Downloads/job-hunter-*.json credentials/google_service_account.json
```

**Step 15:** Install Google dependencies:
```bash
pip install gspread google-auth gspread-formatting
```

**Step 16:** Create a Google Sheet:
- Go to sheets.google.com → Blank spreadsheet
- Name it "Job Hunter — [Name]"
- Rename the first tab to "Job Tracker"
- Copy the Sheet ID from the URL (between /d/ and /edit)

**Step 17:** Share the sheet with the service account:
- Copy the `client_email` from the JSON credentials file
- Click Share on the sheet → paste the email → Editor → Share

**Step 18:** Update the profile:
- Set `STORAGE_MODE = "google"`
- Set `GOOGLE_SHEET_ID = "your_sheet_id"`

**Step 19 (optional):** Install the Apps Script menu:
- In the Google Sheet, go to Extensions → Apps Script
- Delete the default code, paste the contents of `apps_script.js`
- Save, close, reload — a "Job Hunter" menu appears

### Part 4: Create the .env file (optional)

```bash
cp .env.example .env
```

Edit `.env` to set `ACTIVE_PROFILE` (default profile when `--profile` isn't passed).
Add USAJobs API key if desired (optional, free signup).

---

## Daily Usage

### Scrape jobs — API sources (Phase 1A):
```bash
python run_scrape.py --profile alex
```
Scrapes 11 job board APIs + internet-wide search (DuckDuckGo + company career
pages). If the profile has an `ai-training` role, also scrapes AI-training
company boards (xAI Tutors, Mercor, Scale AI... — see `ai_training.py`).
Roles with `"freelance_boards": True` also hit freelance boards
(Freelancer.com API + saved part-time searches — see `scraper_freelance.py`);
their `"max_hours_per_week"` cap filters regular boards to postings with
part-time/contract signals.
With `"boolean_search": True`, also adds clickable LinkedIn/Indeed/Google-X-Ray
Boolean rows per role and best-effort fetches ATS postings the slug lists miss
(see `boolean_query.py`).
After matching, every batch passes through the quality filters
(relevance/USD/budget/aggregator/dedupe — see `quality_filter.py`).
Automatically cleans up stale unapproved jobs older than 30 days.
Results go to `output/{profile}/jobs.csv`.

**Flags:**
- `--web` — Force web search even if `web_search: False` in profile
- `--no-ai` — Skip AI-training sources for this run
- `--no-freelance` — Skip freelance boards for this run
- `--xray` / `--no-xray` — Force Boolean/X-Ray search on / off for this run
- `--role <id>` — Individual check: scrape/match ONE role only (repeatable).
  Skips stale cleanup and drops unmatched pass-through rows. Also available
  per-resume in the admin panel (▶ Run Check on Resumes/Config pages).
- `--no-web` — Skip web search even if `web_search: True` in profile
- `--no-cleanup` — Skip stale job cleanup for this run

### Scrape jobs — LinkedIn + Indeed (Phase 1B):
```bash
python run_scrape_browsers.py --profile alex
```
Uses Playwright to scrape LinkedIn and Indeed. Takes 5-10 minutes. Results
go to a **separate** file: `output/{profile}/browser_jobs.csv`.

This CSV is **informational only — no auto-apply**. It shows:
- Whether Easy Apply / Quick Apply is available
- Direct apply links (where detected)
- Job URL for manual application

### Review the spreadsheet:
Open `jobs.csv` in Excel/Numbers. For each job:
- Check the title, company, salary, location, and work type
- Click the URL to preview the listing
- Put **Y** in the Apply column for ones you want
- Save the file

Also review `browser_jobs.csv` for LinkedIn/Indeed jobs — apply to those manually.

### Apply to jobs (Phase 2):
```bash
# Dry run first — opens browser but doesn't submit anything
python run_apply.py --profile alex --dry-run

# Live run — pauses before each submission for your confirmation
python run_apply.py --profile alex
```

The browser opens visibly. For each job marked "Y" it:
1. Picks the right resume PDF based on role category
2. Navigates to the job URL
3. Detects if it's Easy Apply, form fill, or resume upload
4. Fills fields and attaches the resume
5. Pauses for you to review before submitting

After applying, the Apply column updates to "Done" with today's date.

### Schedule automatic scraping (optional):
```bash
# Mac/Linux cron — every 12 hours (API scrape only, not browser)
crontab -e
0 8,20 * * * cd /path/to/job-hunter && /path/to/venv/bin/python run_scrape.py --profile alex >> output/alex/cron.log 2>&1
```

### Full source list:
See **SOURCES.md** for all 17 job board sources, setup instructions, and
how to add custom companies.

---

## How Job Matching Works (No AI)

The matcher uses two filters:

**Keyword match:** Each role type has `search_queries` like ["IT Manager",
"IT Team Lead"]. The scraper uses these as search terms on the APIs. The
matcher then double-checks that the job title contains words from the query.

**Salary match:** Each role type has `salary_min` and `salary_max`. If a job
lists a salary, it must overlap with the range. If no salary is listed,
the job passes through for manual review.

Jobs that don't match any role type appear as "Unmatched — Review" in the sheet.

**Quality filters (quality_filter.py):** after matching, every batch passes
through configurable hygiene filters — title must contain a role keyword
(catches freelance projects that matched on a stray description word),
non-USD budgets dropped, freelance projects under a budget floor dropped,
web-search aggregator pages ("1,000+ jobs — LinkedIn") dropped, and
duplicates removed by URL *and* normalized title+company (cross-board dupes).
Toggles live in Admin Panel → Config → Result Quality Filters
(`filter_title_relevance`, `filter_usd_only`, `filter_min_budget`,
`filter_aggregators` in SEARCH_SETTINGS). Retro-clean an existing sheet:
`python quality_filter.py --profile alex --clean [--dry-run]` (never touches
rows marked Y/Done).

---

## Apply Method Column

The sheet shows how each job should be applied to:
- ⚡ Easy Apply — one-click (LinkedIn, Indeed)
- 📎 Resume Upload — upload your PDF
- 📋 Form Fill — fill out a form (auto-filled by browser)
- ✍️ Manual — go to the site yourself

---

## Job Board Sources

| Source | Auth | Coverage |
|--------|------|----------|
| Greenhouse API | None | Company career pages (you add slugs) |
| Lever API | None | Startup career pages (you add slugs) |
| Himalayas API | None | Broad remote job search |
| RemoteOK API | None | All remote listings |
| USAJobs API | Free key | US federal government |
| Arbeitnow API | None | EU/US/remote aggregator |
| LinkedIn | Manual URLs | Easy Apply search links (no scraping) |
| Indeed | Manual URLs | Search links (no scraping) |

To add companies to Greenhouse/Lever, edit the slug lists at the top of
`scraper.py`. Find slugs on company career pages.

---

## Adding a New Person (Checklist)

1. `cp profiles/example_profile.py profiles/name.py`
2. Fill in USER_PROFILE (person info) and SEARCH_SETTINGS
3. Add roles to ROLE_PROFILES (as many as needed — one per job category)
4. Drop a resume PDF per role in `output/name/resumes/`
5. `python resume_picker.py --profile name` (verify)
6. `python run_scrape.py --profile name` (first run)
7. If using Google Sheets: create sheet, share with service account, set GOOGLE_SHEET_ID

Or via the admin panel:
1. Open http://localhost:5175 → create person (name, email, location)
2. Add roles one at a time (label, salary range, search queries)
3. Upload a resume PDF for each role

---

## Admin Panel (localhost)

A web-based admin dashboard that connects directly to the project files.
Runs on localhost — no cloud hosting needed. All CLI commands still work
alongside the admin panel.

### Start the Admin Panel:
```bash
source venv/bin/activate
python admin/server.py
# Open http://localhost:5175
```

### Pages:
- **Dashboard** — Job counts, category breakdown, run scrapes
- **Jobs** — View/approve/reject jobs from both CSVs, search, filter, sort
- **AI Training** — AI-training gig setup: platform directory (DataAnnotation, Outlier, Alignerr...) with per-platform signup status tracking, setup checklist, resume generation, and the applicant data used for signups
- **Config** — View profile info, location filter, role profiles, toggle web search & stale cleanup
- **Form Fill** — Edit form auto-fill patterns and dropdown defaults. Seeded
  from `ats_fields.py`, a catalog of the actual fields on Greenhouse, Lever,
  Workday, Ashby, iCIMS, Indeed Apply, and LinkedIn Easy Apply forms
  (labels + "asked on" board tags shown per rule). Dropdown answers support
  `a|b|c` candidates tried in order since option wording differs per ATS.
  Re-seed anytime: "Seed from Job-Board Catalog" button, or
  `python ats_fields.py --profile <name> [--reset]`. New profiles are
  seeded automatically.
- **Resumes** — View all resume PDFs with direct PDF viewer links
- **History** — Scrape/apply run log with timestamps and status
- **Setup** — System checklist (Python, venv, deps, profiles, per-profile status)

### How it works:
- Flask server on port 5175 reads/writes project files directly
- Jobs page edits the CSV files (same as editing in Excel)
- Scrape buttons spawn `run_scrape.py` / `run_scrape_browsers.py` as subprocesses
- Form config edits `output/{profile}/form_config.json`
- No database — filesystem is the database
- No authentication — localhost only (binds to 127.0.0.1)

### Deployment options:
- **Local only (default):** `python admin/server.py` — recommended
- **Deployed multi-user:** `python admin/server.py --deployed` or `DEPLOYED=1`
- **Hosted (VPS/Docker):** See `DEPLOY.md` for full server deployment guide

---

## Troubleshooting

- **"Profile 'x' not found"** → Check `profiles/x.py` exists
- **"No module named..."** → Activate venv: `source venv/bin/activate`
- **Google Sheets permission denied** → Share sheet with service account email
- **Playwright won't launch** → `playwright install chromium`
- **No jobs found** → Check search queries match actual job titles on boards
- **Salary filter too strict** → Widen salary_min/salary_max in the role profile
