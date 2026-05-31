# Job Hunter

Open-source job hunting automation. Scrapes job boards, matches by keyword + salary, tracks in a spreadsheet, and auto-applies with browser automation.

No AI, no cloud services, no API keys required for core functionality. Supports multiple people from a single install.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Features

- **6+ free job board scrapers** — Greenhouse, Lever, Himalayas, RemoteOK, USAJobs, Arbeitnow
- **Extended scrapers** — Workday, The Muse, Wellfound, Adzuna, Google Jobs (SerpAPI)
- **Internet-wide search** — DuckDuckGo + company career pages (Greenhouse, Lever, Workday)
- **Keyword + salary matching** — no AI, no LLM calls, deterministic filtering
- **Stale job cleanup** — auto-removes unapproved jobs older than configurable days
- **Browser automation** — fills forms, uploads resume, pauses before submit
- **Multi-profile** — each person gets isolated config, data, and resumes
- **Two storage backends** — local CSV (zero setup) or Google Sheets (cloud access)
- **Admin panel** — web dashboard for reviewing jobs, managing profiles, running scrapes
- **Deployed mode** — multi-user admin with expandable per-user sections

---

## Architecture

```
Profile (.py)
    |
    v
Scraper (scraper.py / scraper_extended.py / scraper_web.py)
    | hits job board APIs + internet search
    v
Matcher (matcher.py)
    | filters by keyword + salary range
    v
Storage (local_sync.py or sheets_sync.py)
    | writes to CSV or Google Sheet
    v
User reviews spreadsheet, marks jobs Y/N
    |
    v
Auto-Apply (browser_apply.py)
    | opens browser, fills forms, uploads resume
    | pauses before every submission
    v
Job marked "Done" in spreadsheet
```

```
job-hunter/
|-- run_scrape.py            # Entry point: API scraping + web search + stale cleanup
|-- run_scrape_browsers.py   # Entry point: LinkedIn/Indeed scraping
|-- run_tests.py             # Automated test runner
|-- run_apply.py             # Entry point: auto-apply
|-- config.py                # Profile loader
|-- scraper.py               # 6 API scrapers
|-- scraper_extended.py      # 11 extended scrapers
|-- scraper_web.py           # Internet-wide search (DuckDuckGo + career pages)
|-- matcher.py               # Keyword + salary matching
|-- browser_apply.py         # Playwright form automation
|-- storage.py               # Routes to local or Google Sheets
|-- local_sync.py            # CSV backend
|-- sheets_sync.py           # Google Sheets backend
|-- resume_picker.py         # Maps role -> resume PDF
|-- generate_resumes.py      # PDF resume generator
|-- admin/
|   |-- server.py            # Flask admin panel (port 5175)
|   +-- static/index.html    # Single-page dashboard
|-- profiles/
|   |-- example_profile.py   # Template — copy for each person
|   +-- __init__.py
+-- output/{profile}/
    |-- jobs.csv              # API scrape results
    |-- browser_jobs.csv      # Browser scrape results
    |-- form_config.json      # Form auto-fill config
    |-- run_log.json          # Scrape/apply history
    |-- data/                 # Intermediate JSON files
    +-- resumes/              # User's resume PDFs
```

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/YOUR_USERNAME/job-hunter.git
cd job-hunter
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Create Your Profile

```bash
cp profiles/example_profile.py profiles/yourname.py
```

Edit `profiles/yourname.py`:
- `USER_PROFILE` — name, email, phone, skills
- `ROLE_PROFILES` — as many role categories as you want (search queries, salary ranges, resume filenames)
- `SEARCH_SETTINGS` — locations, exclude keywords
- `LOCATION_FILTER` — city, state, nearby cities, include remote

### 3. Add Resumes

Drop one PDF per role in `output/yourname/resumes/` with filenames matching the `resume_file` values in your profile.

### 4. Scrape

```bash
python run_scrape.py --profile yourname          # API + web search + stale cleanup
python run_scrape.py --profile yourname --no-web  # API only, skip web search
python run_scrape.py --profile yourname --no-cleanup  # Skip stale job removal
```

### 5. Review

Open `output/yourname/jobs.csv` in any spreadsheet app. Mark jobs you want to apply to with "Y" in the Apply column.

### 6. Auto-Apply (Dry Run First)

```bash
python run_apply.py --profile yourname --dry-run   # Preview only
python run_apply.py --profile yourname              # Real apply (pauses before submit)
```

---

## Admin Panel

```bash
# Single-user mode (default)
python admin/server.py
# Open http://localhost:5175

# Multi-user deployed mode
python admin/server.py --deployed
# or: DEPLOYED=1 python admin/server.py
```

**Pages:** Dashboard, Jobs, Config, Form Fill, Resumes, History, Setup

**Deployed mode adds:** expandable per-user sections, profile creation, resume upload/delete, global summary stats.

---

## Job Board Sources

| Source | Auth | Cost | Coverage |
|--------|------|------|----------|
| Greenhouse | None | Free | Company career pages (add slugs) |
| Lever | None | Free | Startup career pages (add slugs) |
| Himalayas | None | Free | Remote job aggregator |
| RemoteOK | None | Free | All remote listings |
| USAJobs | Free key | Free | US federal government |
| Arbeitnow | None | Free | EU/US/remote aggregator |
| The Muse | None | Free | Company profiles + jobs |
| Wellfound | None | Free | Startup jobs |
| Adzuna | Free key | Free tier | Multi-country aggregator |
| Google Jobs | SerpAPI key | ~$100/mo | Google Jobs search results |
| LinkedIn | Browser | Free | Easy Apply search links |
| Indeed | Browser | Free | Search links |

---

## Storage Modes

Set `STORAGE_MODE` in your profile:

| Mode | Setup | Access |
|------|-------|--------|
| `"local"` (default) | None | CSV file, open in any spreadsheet app |
| `"google"` | Service account + Sheet ID | Google Sheets, cloud access, in-sheet menus |

Both modes can coexist — they write to different targets.

---

## Environment Variables

All optional. Set in `.env` file (gitignored).

| Variable | Purpose |
|----------|---------|
| `USAJOBS_API_KEY` | USAJobs API (free, get from developer.usajobs.gov) |
| `USAJOBS_EMAIL` | Required with USAJobs API key |
| `SERPAPI_KEY` | Google Jobs via SerpAPI (~$100/mo) |
| `ADZUNA_APP_ID` | Adzuna API (free tier available) |
| `ADZUNA_APP_KEY` | Adzuna API key |
| `GOOGLE_SHEET_ID` | Google Sheets mode — target sheet ID |
| `DEPLOYED` | Set to `1` for multi-user admin panel mode |

---

## Multi-Profile

Each person gets isolated data:

```bash
cp profiles/example_profile.py profiles/jane.py
# Edit jane.py, add resumes to output/jane/resumes/
python run_scrape.py --profile jane
python run_apply.py --profile jane --dry-run
```

---

## Hosting / Deployment

See **[DEPLOY.md](DEPLOY.md)** for full deployment instructions:

- **Linux VPS** (DigitalOcean, Linode, AWS) — systemd + Nginx + HTTPS + basic auth
- **Docker** — Dockerfile + docker-compose.yml included
- **PythonAnywhere** — free tier, admin panel only (no auto-apply)

Deployed mode enables multi-user features: expandable per-user sections, profile creation, resume upload/delete.

```bash
# Start in deployed mode
python admin/server.py --deployed
# or: DEPLOYED=1 python admin/server.py
```

---

## Documentation

| File | Purpose |
|------|---------|
| [DEPLOY.md](DEPLOY.md) | Local setup + hosted deployment (VPS, Docker, PythonAnywhere) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Architecture, data flow, how to add sources |
| [MAINTENANCE.md](MAINTENANCE.md) | Module-by-module reference for contributors |
| [TESTING.md](TESTING.md) | 40+ manual test scenarios + automated test runner |
| [HEALTH_CHECK.md](HEALTH_CHECK.md) | Quick diagnostic commands |
| [FUTURE.md](FUTURE.md) | Roadmap and planned features |
| [BUG_TRACKER.md](BUG_TRACKER.md) | Known bugs and reporting |
| [SECURITY.md](SECURITY.md) | Vulnerability reporting policy |
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Community guidelines |
| [SOURCES.md](SOURCES.md) | Job board API details |
| [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md) | Step-by-step setup guide |
| [APP_PLAYBOOK.md](APP_PLAYBOOK.md) | Single-source codebase reference |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | Non-technical user guide |

---

## Security Notes

- Admin panel binds to `127.0.0.1` only — do not expose to the internet without adding auth
- Profile files are executed as Python code — only load profiles you trust
- `.env` and profile files are gitignored — never commit API keys or personal info
- See [SECURITY.md](SECURITY.md) for vulnerability reporting

---

## License

[MIT](LICENSE) — Copyright (c) 2026 Alexander Moody
