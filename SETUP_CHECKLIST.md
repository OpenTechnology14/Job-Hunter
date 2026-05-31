# Setup Checklist

Track setup progress per installation. Copy this file or check off items as you go.
The Admin Panel at http://localhost:5175 (Setup tab) auto-detects most of these.

---

## Core Setup

- [ ] **Python 3.10+ installed**
  - Check: `python3 --version`
  - Install: `brew install python@3.12` (Mac) or python.org (Windows)

- [ ] **Virtual environment created**
  - `python3.12 -m venv venv && source venv/bin/activate`

- [ ] **Dependencies installed**
  - `pip install -r requirements.txt`

- [ ] **Playwright + Chromium installed**
  - `pip install playwright && playwright install chromium`

- [ ] **.env file created**
  - `cp .env.example .env`
  - Set `ACTIVE_PROFILE` to default profile name

---

## Per-Person Setup

### Person: ________________

- [ ] **Profile created**
  - `cp profiles/example_profile.py profiles/{name}.py`

- [ ] **Profile configured**
  - [ ] USER_PROFILE filled (name, email, phone, skills)
  - [ ] ROLE_PROFILES defined (at least 1 role with search queries + salary range)
  - [ ] SEARCH_SETTINGS configured (locations, exclude keywords)
  - [ ] LOCATION_FILTER set (city, state, radius, nearby_cities)
  - [ ] STORAGE_MODE set to "local"

- [ ] **Resumes created and placed** (one PDF per role)
  - [ ] Drop PDFs in `output/{name}/resumes/` matching each role's `resume_file`
  - Verify: `python resume_picker.py --profile {name}`

- [ ] **Form fill config created**
  - `cp form_config_example.json output/{name}/form_config.json`
  - Edit with custom form field mappings

- [ ] **First API scrape run**
  - `python run_scrape.py --profile {name}`
  - Verify: `output/{name}/jobs.csv` has results

- [ ] **First browser scrape run (optional)**
  - `python run_scrape_browsers.py --profile {name}`
  - Verify: `output/{name}/browser_jobs.csv` has results

- [ ] **Auto-apply tested (dry run)**
  - Mark a job with Y in Apply column, save CSV
  - `python run_apply.py --profile {name} --dry-run`

---

## Optional API Keys

- [ ] **USAJobs** (free) — `USAJOBS_API_KEY` + `USAJOBS_EMAIL` in `.env`
  - Sign up: https://developer.usajobs.gov/

- [ ] **Adzuna** (free) — `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` in `.env`
  - Sign up: https://developer.adzuna.com/

- [ ] **SerpAPI / Google Jobs** (paid ~$100/mo) — `SERPAPI_KEY` in `.env`
  - Sign up: https://serpapi.com/

---

## Optional Integrations

- [ ] **Google Sheets mode** (instead of local CSV)
  - See CLAUDE.md Part 3 for full setup
  - Set `STORAGE_MODE = "google"` in profile

- [ ] **Cron scheduling** (automatic scraping)
  - `crontab -e`
  - Add: `0 8,20 * * * cd /path/to/job-hunter && /path/to/venv/bin/python run_scrape.py --profile {name}`

- [ ] **Claude Chrome Extension** (for LinkedIn/Indeed manual apply)
  - Install Claude in Chrome extension
  - Open `browser_jobs.csv`, filter Apply = Y
  - Use extension to assist with applications on those job pages

---

## Admin Panel

- [ ] **Admin Panel running**
  - `python admin/server.py` → http://localhost:5175
  - Deployed mode: `python admin/server.py --deployed`
  - See `DEPLOY.md` for server hosting guide

---

## Current Installation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Python | | |
| Venv | | |
| Playwright | | |
| Profile: alex | | |
| Profile: marcelli | | |
| API Keys | | |
| Cron | | |
| Admin Panel | | |

Last updated: ________________
