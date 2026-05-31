# Job Board Sources — Setup & Configuration

This document covers all job board sources in the system, how to enable them,
and what each requires.

---

## Source Overview

| # | Source | Type | Auth Required | Best For |
|---|--------|------|---------------|----------|
| 1 | Greenhouse API | JSON API | None | Tech companies (add slugs) |
| 2 | Lever API | JSON API | None | Startups (add slugs) |
| 3 | Himalayas API | JSON API | None | Remote jobs (broad) |
| 4 | RemoteOK API | JSON API | None | Remote-only listings |
| 5 | USAJobs API | JSON API | Free key | US federal government |
| 6 | Arbeitnow API | JSON API | None | EU/US/remote aggregator |
| 7 | Workday | Structured API | None | Large employers, hospitals |
| 8 | The Muse | JSON API | None | Mid-market companies |
| 9 | Wellfound | API | None | Startups, remote |
| 10 | Adzuna | JSON API | Free key | UK/US aggregator |
| 11 | Google Jobs | SerpAPI | Paid key ($100/mo) | Aggregates everything |
| 12 | Indeed | Playwright | None | Largest US job board |
| 13 | LinkedIn | Playwright | None | Professional jobs |
| 14 | Dice | Playwright | None | Tech/IT-specific |
| 15 | ZipRecruiter | Playwright | None | Large US market |
| 16 | SimplyHired | Playwright | None | Indeed-owned aggregator |
| 17 | Health eCareers | Playwright | None | Healthcare-specific |

---

## Two Scrape Commands

### `run_scrape.py` — API-based (fast, reliable)

```bash
python run_scrape.py --profile alex
```

Uses sources 1-11. Fast (1-3 minutes). Results go to `output/{profile}/jobs.csv`.
These jobs ARE eligible for auto-apply via `run_apply.py`.

### `run_scrape_browsers.py` — Playwright-based (LinkedIn + Indeed)

```bash
python run_scrape_browsers.py --profile alex
```

Uses sources 12-13 (Indeed + LinkedIn). Slower (5-10 minutes). Results go to
a SEPARATE file: `output/{profile}/browser_jobs.csv`.

These jobs are **informational only — no auto-apply**. The CSV shows:
- Whether Easy Apply / Quick Apply is available
- Direct apply links (where detected)
- Job URL for manual application

---

## Setup by Source

### Sources 1-4, 6 (No setup needed)
These work immediately with zero configuration.

### Source 5: USAJobs (free key)
1. Sign up at https://developer.usajobs.gov/
2. Add to `.env`:
```
USAJOBS_API_KEY=your_key
USAJOBS_EMAIL=your_email@example.com
```

### Source 7: Workday (add companies)
Edit `WORKDAY_COMPANIES` in `scraper_extended.py` to add employers.
Find the tenant/site by visiting a company's career page — Workday URLs
look like: `companyname.wd5.myworkdayjobs.com`

Pre-configured companies:
- Dartmouth Health (NH)
- Elliot Hospital / Solution Health (NH)
- Amazon, Deloitte, Accenture, Fidelity, Liberty Mutual, BAE Systems

### Source 10: Adzuna (free key)
1. Sign up at https://developer.adzuna.com/
2. Add to `.env`:
```
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

### Source 11: Google Jobs via SerpAPI (paid)
1. Sign up at https://serpapi.com/ (~$100/mo for 5k searches)
2. Add to `.env`:
```
SERPAPI_KEY=your_key
```
This is the single most comprehensive source — it aggregates Indeed, LinkedIn,
Glassdoor, ZipRecruiter, and hundreds of company sites into one API.

### Sources 12-17: Playwright scrapers
No API keys needed. Requires Playwright + Chromium:
```bash
pip install playwright
playwright install chromium
```

**Important notes about Playwright scrapers:**
- They render real browser pages, so they're slower
- Sites may change their HTML structure — scrapers may need updating
- Some sites have bot detection (CAPTCHAs, rate limiting)
- LinkedIn may require login for full results (public listings are limited)
- Run during off-peak hours for best results

---

## Adding Custom Companies

### Greenhouse
Edit `GREENHOUSE_COMPANIES` in `scraper.py`:
```python
GREENHOUSE_COMPANIES = [
    "companyslug",  # Find at: boards.greenhouse.io/companyslug
]
```

### Lever
Edit `LEVER_COMPANIES` in `scraper.py`:
```python
LEVER_COMPANIES = [
    "companyslug",  # Find at: jobs.lever.co/companyslug
]
```

### Workday
Edit `WORKDAY_COMPANIES` in `scraper_extended.py`:
```python
WORKDAY_COMPANIES = [
    {"name": "Display Name", "tenant": "tenant_id", "site": "site_slug"},
    # URL pattern: site_slug.wd5.myworkdayjobs.com
]
```

---

## Location Filtering

All scraped jobs pass through a location filter before being added to CSVs.
Only **Remote** jobs and jobs **within radius** of your configured city are kept.

Configure in your profile file (`profiles/yourname.py`):

```python
LOCATION_FILTER = {
    "city": "Nashua",           # Your city
    "state": "NH",              # Your state abbreviation
    "radius_miles": 20,         # Approximate radius
    "nearby_cities": [          # Cities within radius
        "Manchester", "Merrimack", "Hudson", "Lowell",
        # ... add more as needed
    ],
    "include_remote": True,     # Set False to exclude remote jobs
}
```

To relocate the whole automation:
1. Change `city` and `state`
2. Update `nearby_cities` with towns within your radius
3. Update `SEARCH_SETTINGS["locations"]` to match
4. Re-run scrape — old CSV is preserved, new jobs are appended

---

## Rate Limiting & Bot Detection

| Source | Rate Limit | Notes |
|--------|-----------|-------|
| Greenhouse | None observed | 0.3s delay between companies |
| Lever | None observed | 0.3s delay between companies |
| Himalayas | None observed | Very generous |
| RemoteOK | Soft (no key) | Cached locally per session |
| USAJobs | 200 req/day | Generous for personal use |
| Arbeitnow | None observed | 0.5s delay between pages |
| Indeed | Aggressive | May show CAPTCHAs |
| LinkedIn | Moderate | Limited without login |
| Dice | Light | Generally reliable |
| ZipRecruiter | Moderate | May block headless browsers |

**Best practices:**
- Don't run browser scrapes more than 2x/day
- API scrapes are safe to run every 12 hours
- If a Playwright scraper returns 0 results, the site may have detected the bot
- Retry once; if still 0, the scraper may need its selectors updated

---

## Troubleshooting

- **"Playwright not installed"** → `pip install playwright && playwright install chromium`
- **Indeed shows 0 jobs** → Bot detection. Try again in a few hours or from a different network.
- **LinkedIn shows limited results** → Public listings are capped. Login not supported in automation.
- **Workday returns nothing** → The tenant/site values may be wrong. Check the company's actual career URL.
- **Adzuna/SerpAPI returns nothing** → Check your API keys in `.env`
- **A scraper that used to work now returns 0** → The site likely changed its HTML. Check selectors in `scraper_extended.py` or `run_scrape_browsers.py`.
