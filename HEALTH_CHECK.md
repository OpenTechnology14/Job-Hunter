# Job Hunter — Health Check

Quick diagnostic commands. Run these when something isn't working.

---

## 1. Environment

```bash
# Python version (need 3.8+)
python --version

# Virtual env active?
which python
# Should point to venv/bin/python, not system Python

# Dependencies installed?
pip list | grep -E "requests|playwright|flask|fpdf2|python-dotenv"

# Playwright browsers installed?
playwright install --dry-run
```

---

## 2. Profile

```bash
# Profile loads without errors?
python -c "from config import load_profile; p = load_profile('yourname'); print('OK')"

# Resume files exist?
ls -la output/yourname/resumes/

# Output directory structure?
ls -la output/yourname/
# Should have: jobs.csv, data/, resumes/, form_config.json, run_log.json
```

---

## 3. Scraping

```bash
# Quick test — single source
python -c "
from scraper import scrape_himalayas
jobs = scrape_himalayas(['software engineer'], 'Remote', max_results=5)
print(f'{len(jobs)} jobs found')
if jobs: print(jobs[0]['title'], '-', jobs[0]['company'])
"

# Full scrape with output
python run_scrape.py --profile yourname
# Should print job counts per source and total

# Check CSV output
head -5 output/yourname/jobs.csv
```

---

## 4. Admin Panel

```bash
# Server starts?
python admin/server.py
# Should print "Open http://localhost:5175"

# API responds?
curl -s http://localhost:5175/api/profiles | python -m json.tool

# Port in use?
lsof -i :5175
# Kill if stuck: lsof -ti:5175 | xargs kill -9
```

---

## 5. Browser Automation

```bash
# Playwright works?
python -c "from playwright.sync_api import sync_playwright; print('OK')"

# Dry run (no submit)
python run_apply.py --profile yourname --dry-run
# Browser should open, navigate to first Y job, fill form, NOT submit
```

---

## 6. Google Sheets (Optional)

```bash
# Credentials file exists?
ls credentials/*.json

# Sheet ID configured?
python -c "
from config import load_profile
p = load_profile('yourname')
print('Sheet ID:', p.get('GOOGLE_SHEET_ID', 'NOT SET'))
print('Storage:', p.get('STORAGE_MODE', 'local'))
"

# Test connection
python -c "
from sheets_sync import connect_sheet
sheet = connect_sheet('YOUR_SHEET_ID')
print(f'Connected: {sheet.title}')
"
```

---

## Common Fixes

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError` | Activate venv: `source venv/bin/activate` |
| `Profile not found` | Check filename matches: `ls profiles/` |
| `Connection refused` on admin | Server not running or wrong port |
| `0 jobs found` from all sources | Check internet connection, then check API response format changes |
| Browser doesn't open | Run `playwright install chromium` |
| CSV has wrong columns | Check `SHEET_COLUMNS` in storage module matches your version |
| Port 5175 in use | `lsof -ti:5175 \| xargs kill -9` |
