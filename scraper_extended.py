"""
Extended Job Board Scrapers — Playwright-based + additional APIs.

These supplement the API-only scrapers in scraper.py by adding boards
that require browser rendering or have different API patterns.

Sources:
  7.  Indeed        — Playwright browser scrape
  8.  Dice          — Playwright browser scrape (tech-focused)
  9.  ZipRecruiter  — Playwright browser scrape
  10. SimplyHired   — Playwright browser scrape
  11. Google Jobs   — via SerpAPI (paid, optional) or Playwright fallback
  12. Wellfound     — GraphQL API (startup/remote jobs)
  13. The Muse      — Free JSON API (no auth)
  14. Adzuna        — Free JSON API (free key, sign up)
  15. Health eCareers — Playwright browser scrape (healthcare-specific)
  16. Workday       — Per-company structured API endpoints
  17. LinkedIn      — Playwright browser scrape (public listings only)

Usage:
    Called from scraper.py via scrape_extended_sources()
"""
import json
import os
import re
import time
import hashlib
from datetime import datetime

import requests

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

from scraper import JobListing, HEADERS


# ═══════════════════════════════════════════════════════════
# Shared Playwright helpers
# ═══════════════════════════════════════════════════════════

_browser_instance = None
_browser_context = None


def _get_browser():
    global _browser_instance, _browser_context
    if not HAS_PLAYWRIGHT:
        return None, None
    if _browser_instance is None:
        pw = sync_playwright().start()
        _browser_instance = pw.chromium.launch(headless=True)
        _browser_context = _browser_instance.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
    return _browser_instance, _browser_context


def _close_browser():
    global _browser_instance, _browser_context
    if _browser_instance:
        try:
            _browser_instance.close()
        except Exception:
            pass
        _browser_instance = None
        _browser_context = None


def _safe_text(el, default=""):
    try:
        return (el.inner_text() or default).strip()
    except Exception:
        return default


# ═══════════════════════════════════════════════════════════
# Indeed (Playwright scrape)
# ═══════════════════════════════════════════════════════════

def scrape_indeed(query: str, location: str = "", max_results: int = 25) -> list[JobListing]:
    if not HAS_PLAYWRIGHT:
        return []
    jobs = []
    try:
        _, ctx = _get_browser()
        page = ctx.new_page()

        params = f"q={requests.utils.quote(query)}&sort=date&fromage=7"
        if location:
            params += f"&l={requests.utils.quote(location)}"
        url = f"https://www.indeed.com/jobs?{params}"

        page.goto(url, timeout=20000)
        page.wait_for_timeout(3000)

        cards = page.query_selector_all("div.job_seen_beacon, div.jobsearch-ResultsList > div[data-jk]")
        for card in cards[:max_results]:
            try:
                title_el = card.query_selector("h2.jobTitle a, h2.jobTitle span")
                company_el = card.query_selector("[data-testid='company-name'], span.companyName")
                location_el = card.query_selector("[data-testid='text-location'], div.companyLocation")
                salary_el = card.query_selector("div.salary-snippet-container, div.metadata.salary-snippet-container")
                link_el = card.query_selector("h2.jobTitle a, a.jcs-JobTitle")

                title = _safe_text(title_el)
                if not title:
                    continue

                href = ""
                if link_el:
                    href = link_el.get_attribute("href") or ""
                    if href.startswith("/"):
                        href = f"https://www.indeed.com{href}"

                jobs.append(JobListing(
                    title=title,
                    company=_safe_text(company_el, "Unknown"),
                    location=_safe_text(location_el),
                    salary=_safe_text(salary_el),
                    url=href,
                    source="Indeed",
                    apply_method="📎 Resume Upload",
                ))
            except Exception:
                continue

        page.close()
    except Exception as e:
        print(f"    [Indeed] Error: {e}")

    print(f"  [Indeed] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# Dice (Playwright scrape — tech-focused)
# ═══════════════════════════════════════════════════════════

def scrape_dice(query: str, location: str = "", max_results: int = 25) -> list[JobListing]:
    if not HAS_PLAYWRIGHT:
        return []
    jobs = []
    try:
        _, ctx = _get_browser()
        page = ctx.new_page()

        params = f"q={requests.utils.quote(query)}&countryCode=US&radius=30&radiusUnit=mi&pageSize={max_results}&language=en&eid=S2Q_"
        if location:
            params += f"&location={requests.utils.quote(location)}"
        url = f"https://www.dice.com/jobs?{params}"

        page.goto(url, timeout=20000)
        page.wait_for_timeout(3000)

        cards = page.query_selector_all("dhi-search-card")
        for card in cards[:max_results]:
            try:
                title_el = card.query_selector("a.card-title-link")
                company_el = card.query_selector("a[data-cy='search-result-company-name']")
                location_el = card.query_selector("span[data-cy='search-result-location']")
                salary_el = card.query_selector("span[data-cy='search-result-salary']")

                title = _safe_text(title_el)
                if not title:
                    continue

                href = ""
                if title_el:
                    href = title_el.get_attribute("href") or ""
                    if href and not href.startswith("http"):
                        href = f"https://www.dice.com{href}"

                jobs.append(JobListing(
                    title=title,
                    company=_safe_text(company_el, "Unknown"),
                    location=_safe_text(location_el),
                    salary=_safe_text(salary_el),
                    url=href,
                    source="Dice",
                    apply_method="📎 Resume Upload",
                ))
            except Exception:
                continue

        page.close()
    except Exception as e:
        print(f"    [Dice] Error: {e}")

    print(f"  [Dice] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# ZipRecruiter (Playwright scrape)
# ═══════════════════════════════════════════════════════════

def scrape_ziprecruiter(query: str, location: str = "", max_results: int = 25) -> list[JobListing]:
    if not HAS_PLAYWRIGHT:
        return []
    jobs = []
    try:
        _, ctx = _get_browser()
        page = ctx.new_page()

        params = f"search={requests.utils.quote(query)}&days=7"
        if location:
            params += f"&location={requests.utils.quote(location)}"
        url = f"https://www.ziprecruiter.com/jobs-search?{params}"

        page.goto(url, timeout=20000)
        page.wait_for_timeout(3000)

        cards = page.query_selector_all("article.job_result, div.job_content")
        if not cards:
            cards = page.query_selector_all("[class*='JobCard'], [data-testid='job-card']")

        for card in cards[:max_results]:
            try:
                title_el = card.query_selector("h2 a, a[class*='job_link'], [class*='title'] a")
                company_el = card.query_selector("a[class*='company'], [class*='company_name'], p.company_name")
                location_el = card.query_selector("[class*='location'], span.location")
                salary_el = card.query_selector("[class*='salary'], span.salary")

                title = _safe_text(title_el)
                if not title:
                    continue

                href = ""
                if title_el:
                    href = title_el.get_attribute("href") or ""

                jobs.append(JobListing(
                    title=title,
                    company=_safe_text(company_el, "Unknown"),
                    location=_safe_text(location_el),
                    salary=_safe_text(salary_el),
                    url=href,
                    source="ZipRecruiter",
                    apply_method="📎 Resume Upload",
                ))
            except Exception:
                continue

        page.close()
    except Exception as e:
        print(f"    [ZipRecruiter] Error: {e}")

    print(f"  [ZipRecruiter] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# SimplyHired (Playwright scrape)
# ═══════════════════════════════════════════════════════════

def scrape_simplyhired(query: str, location: str = "", max_results: int = 25) -> list[JobListing]:
    if not HAS_PLAYWRIGHT:
        return []
    jobs = []
    try:
        _, ctx = _get_browser()
        page = ctx.new_page()

        params = f"q={requests.utils.quote(query)}"
        if location:
            params += f"&l={requests.utils.quote(location)}"
        url = f"https://www.simplyhired.com/search?{params}"

        page.goto(url, timeout=20000)
        page.wait_for_timeout(3000)

        cards = page.query_selector_all("article[data-testid='searchSerpJob'], li.SerpJob-jobCard, div.SerpJob-jobCard")
        if not cards:
            cards = page.query_selector_all("[class*='jobposting'], article.job")

        for card in cards[:max_results]:
            try:
                title_el = card.query_selector("h2 a, a[class*='jobTitle'], h3 a")
                company_el = card.query_selector("[data-testid='companyName'], span.jobposting-company, [class*='company']")
                location_el = card.query_selector("[data-testid='searchSerpJobLocation'], span.jobposting-location, [class*='location']")
                salary_el = card.query_selector("[data-testid='searchSerpJobSalary'], span.jobposting-salary, [class*='salary']")

                title = _safe_text(title_el)
                if not title:
                    continue

                href = ""
                if title_el:
                    href = title_el.get_attribute("href") or ""
                    if href.startswith("/"):
                        href = f"https://www.simplyhired.com{href}"

                jobs.append(JobListing(
                    title=title,
                    company=_safe_text(company_el, "Unknown"),
                    location=_safe_text(location_el),
                    salary=_safe_text(salary_el),
                    url=href,
                    source="SimplyHired",
                    apply_method="📎 Resume Upload",
                ))
            except Exception:
                continue

        page.close()
    except Exception as e:
        print(f"    [SimplyHired] Error: {e}")

    print(f"  [SimplyHired] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# LinkedIn (Playwright scrape — public listings, no login)
# ═══════════════════════════════════════════════════════════

def scrape_linkedin(query: str, location: str = "", max_results: int = 25) -> list[JobListing]:
    if not HAS_PLAYWRIGHT:
        return []
    jobs = []
    try:
        _, ctx = _get_browser()
        page = ctx.new_page()

        params = f"keywords={requests.utils.quote(query)}&f_TPR=r604800&sortBy=DD"
        if location:
            params += f"&location={requests.utils.quote(location)}"
        url = f"https://www.linkedin.com/jobs/search/?{params}"

        page.goto(url, timeout=20000)
        page.wait_for_timeout(4000)

        # Scroll to load more cards
        for _ in range(3):
            page.evaluate("window.scrollBy(0, 800)")
            page.wait_for_timeout(1000)

        cards = page.query_selector_all("div.base-card, li.result-card, div.job-search-card")
        for card in cards[:max_results]:
            try:
                title_el = card.query_selector("h3.base-search-card__title, h3.result-card__title")
                company_el = card.query_selector("h4.base-search-card__subtitle, h4.result-card__subtitle")
                location_el = card.query_selector("span.job-search-card__location")
                link_el = card.query_selector("a.base-card__full-link, a.result-card__full-link")
                date_el = card.query_selector("time")
                salary_el = card.query_selector("span.job-search-card__salary-info")

                title = _safe_text(title_el)
                if not title:
                    continue

                href = ""
                if link_el:
                    href = link_el.get_attribute("href") or ""

                jobs.append(JobListing(
                    title=title,
                    company=_safe_text(company_el, "Unknown"),
                    location=_safe_text(location_el),
                    salary=_safe_text(salary_el),
                    url=href.split("?")[0] if href else "",
                    source="LinkedIn",
                    date_posted=date_el.get_attribute("datetime") if date_el else "",
                    apply_method="📎 Resume Upload",
                ))
            except Exception:
                continue

        page.close()
    except Exception as e:
        print(f"    [LinkedIn] Error: {e}")

    print(f"  [LinkedIn] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# Health eCareers (Playwright scrape — healthcare-specific)
# ═══════════════════════════════════════════════════════════

def scrape_health_ecareers(query: str, location: str = "", max_results: int = 25) -> list[JobListing]:
    if not HAS_PLAYWRIGHT:
        return []
    jobs = []
    try:
        _, ctx = _get_browser()
        page = ctx.new_page()

        params = f"keyword={requests.utils.quote(query)}&radius=30"
        if location:
            params += f"&location={requests.utils.quote(location)}"
        url = f"https://www.healthecareers.com/jobs/search?{params}"

        page.goto(url, timeout=20000)
        page.wait_for_timeout(3000)

        cards = page.query_selector_all("div.job-listing-item, article.job-card, div.search-result-item")
        if not cards:
            cards = page.query_selector_all("[class*='job-result'], [class*='JobCard']")

        for card in cards[:max_results]:
            try:
                title_el = card.query_selector("h2 a, a.job-title, [class*='title'] a")
                company_el = card.query_selector("[class*='company'], [class*='employer'], span.company")
                location_el = card.query_selector("[class*='location'], span.location")

                title = _safe_text(title_el)
                if not title:
                    continue

                href = ""
                if title_el:
                    href = title_el.get_attribute("href") or ""
                    if href.startswith("/"):
                        href = f"https://www.healthecareers.com{href}"

                jobs.append(JobListing(
                    title=title,
                    company=_safe_text(company_el, "Unknown"),
                    location=_safe_text(location_el),
                    url=href,
                    source="HealthECareers",
                    apply_method="📎 Resume Upload",
                ))
            except Exception:
                continue

        page.close()
    except Exception as e:
        print(f"    [HealthECareers] Error: {e}")

    print(f"  [HealthECareers] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# Google Jobs via SerpAPI (paid, optional — $100/mo for 5k searches)
# Sign up: https://serpapi.com — set SERPAPI_KEY in .env
# Falls back to skip if no key.
# ═══════════════════════════════════════════════════════════

def scrape_google_jobs(query: str, location: str = "", max_results: int = 25) -> list[JobListing]:
    api_key = os.getenv("SERPAPI_KEY", "")
    if not api_key:
        return []

    jobs = []
    try:
        params = {
            "engine": "google_jobs",
            "q": query,
            "api_key": api_key,
            "num": min(max_results, 40),
        }
        if location:
            params["location"] = location

        resp = requests.get("https://serpapi.com/search", params=params, timeout=15)
        if resp.status_code != 200:
            return jobs

        for item in resp.json().get("jobs_results", []):
            salary = ""
            if item.get("detected_extensions", {}).get("salary"):
                salary = item["detected_extensions"]["salary"]

            jobs.append(JobListing(
                title=item.get("title", ""),
                company=item.get("company_name", "Unknown"),
                location=item.get("location", ""),
                salary=salary,
                url=item.get("apply_options", [{}])[0].get("link", "") if item.get("apply_options") else "",
                source="Google Jobs",
                description=item.get("description", "")[:1500],
                apply_method="📎 Resume Upload",
            ))
    except Exception as e:
        print(f"    [Google Jobs] Error: {e}")

    print(f"  [Google Jobs] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# The Muse (free JSON API, no auth)
# Good for mid-market companies.
# ═══════════════════════════════════════════════════════════

def scrape_themuse(query: str, location: str = "", max_results: int = 25) -> list[JobListing]:
    jobs = []
    try:
        params = {
            "page": 1,
            "descending": "true",
        }
        if location:
            params["location"] = location

        url = "https://www.themuse.com/api/public/jobs"
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return jobs

        query_lower = query.lower()
        for item in resp.json().get("results", []):
            title = item.get("name", "")
            if query_lower not in title.lower():
                continue

            loc_parts = [l.get("name", "") for l in item.get("locations", [])]
            company_obj = item.get("company", {})

            jobs.append(JobListing(
                title=title,
                company=company_obj.get("name", "Unknown"),
                location=", ".join(loc_parts),
                url=f"https://www.themuse.com/jobs/{item.get('short_name', item.get('id', ''))}",
                source="The Muse",
                description=re.sub(r"<[^>]+>", " ", item.get("contents", ""))[:1500],
                date_posted=item.get("publication_date", ""),
                apply_method="📎 Resume Upload",
            ))
            if len(jobs) >= max_results:
                break

    except Exception as e:
        print(f"    [The Muse] Error: {e}")

    print(f"  [The Muse] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# Adzuna (free JSON API — requires free app_id + app_key)
# Sign up: https://developer.adzuna.com — set in .env
# ═══════════════════════════════════════════════════════════

def scrape_adzuna(query: str, location: str = "", max_results: int = 25) -> list[JobListing]:
    app_id = os.getenv("ADZUNA_APP_ID", "")
    app_key = os.getenv("ADZUNA_APP_KEY", "")
    if not app_id or not app_key:
        return []

    jobs = []
    try:
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "what": query,
            "results_per_page": min(max_results, 50),
            "max_days_old": 7,
            "sort_by": "date",
            "content-type": "application/json",
        }
        if location:
            params["where"] = location

        resp = requests.get(
            "https://api.adzuna.com/v1/api/jobs/us/search/1",
            params=params, timeout=15,
        )
        if resp.status_code != 200:
            return jobs

        for item in resp.json().get("results", []):
            salary = ""
            if item.get("salary_min") and item.get("salary_max"):
                salary = f"${int(item['salary_min']):,} - ${int(item['salary_max']):,}"
            elif item.get("salary_min"):
                salary = f"${int(item['salary_min']):,}+"

            jobs.append(JobListing(
                title=item.get("title", ""),
                company=item.get("company", {}).get("display_name", "Unknown"),
                location=item.get("location", {}).get("display_name", ""),
                salary=salary,
                url=item.get("redirect_url", ""),
                source="Adzuna",
                description=item.get("description", "")[:1500],
                date_posted=item.get("created", ""),
                apply_method="📎 Resume Upload",
            ))
    except Exception as e:
        print(f"    [Adzuna] Error: {e}")

    print(f"  [Adzuna] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# Wellfound / AngelList (GraphQL API — startup jobs)
# ═══════════════════════════════════════════════════════════

def scrape_wellfound(query: str, max_results: int = 25) -> list[JobListing]:
    jobs = []
    try:
        resp = requests.get(
            f"https://wellfound.com/api/search/jobs?query={requests.utils.quote(query)}",
            headers={
                "User-Agent": HEADERS["User-Agent"],
                "Accept": "application/json",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return jobs

        for item in resp.json().get("results", resp.json().get("jobs", [])):
            title = item.get("title", item.get("name", ""))
            if not title:
                continue

            company = item.get("company", {})
            salary = ""
            if item.get("salary_min") and item.get("salary_max"):
                salary = f"${int(item['salary_min']):,} - ${int(item['salary_max']):,}"

            location = item.get("location", "")
            if item.get("remote"):
                location = f"Remote — {location}" if location else "Remote"

            jobs.append(JobListing(
                title=title,
                company=company.get("name", "Unknown") if isinstance(company, dict) else str(company),
                location=location,
                salary=salary,
                url=item.get("url", ""),
                source="Wellfound",
                apply_method="📎 Resume Upload",
            ))
            if len(jobs) >= max_results:
                break

    except Exception as e:
        print(f"    [Wellfound] Error: {e}")

    print(f"  [Wellfound] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# Workday (per-company structured endpoints)
# Add company configs below. These are large employers that
# use Workday for their career sites.
# ═══════════════════════════════════════════════════════════

# Workday company configs. To find the correct tenant/site for a company:
# 1. Go to the company's career page
# 2. Look for URLs like: companyname.wd5.myworkdayjobs.com/en-US/SiteName
# 3. The "wd5" part is the subdomain (wd1-wd12 are common)
# 4. "SiteName" after /en-US/ is the site value
# 5. The tenant is usually the company name portion
#
# Example: https://bofa.wd1.myworkdayjobs.com/en-US/BofA_Careers
#   → {"name": "Bank of America", "tenant": "bofa", "site": "BofA_Careers", "wd": "wd1"}
WORKDAY_COMPANIES = [
    # Add companies as you find their Workday URLs.
    # Each company's URL pattern is unique — there's no way to guess them.
    # {"name": "Company", "tenant": "slug", "site": "CareerSite", "wd": "wd5"},
]


def scrape_workday(query: str, location: str = "", max_results: int = 25) -> list[JobListing]:
    jobs = []
    query_lower = query.lower()

    for company in WORKDAY_COMPANIES:
        try:
            wd = company.get("wd", "wd5")
            search_url = (
                f"https://{company['tenant']}.{wd}.myworkdayjobs.com"
                f"/wday/cxs/{company['tenant']}/{company['site']}/jobs"
            )
            payload = {
                "appliedFacets": {},
                "limit": min(max_results, 20),
                "offset": 0,
                "searchText": query,
            }
            if location:
                payload["searchText"] = f"{query} {location}"

            resp = requests.post(
                search_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": HEADERS["User-Agent"],
                },
                timeout=10,
            )
            if resp.status_code != 200:
                continue

            data = resp.json()
            for posting in data.get("jobPostings", []):
                title = posting.get("title", "")
                if query_lower not in title.lower():
                    continue

                loc = posting.get("locationsText", "")
                ext_path = posting.get("externalPath", "")
                job_url = f"https://{company['tenant']}.{wd}.myworkdayjobs.com{ext_path}" if ext_path else ""

                jobs.append(JobListing(
                    title=title,
                    company=company["name"],
                    location=loc,
                    url=job_url,
                    source="Workday",
                    date_posted=posting.get("postedOn", ""),
                    apply_method="📋 Form Fill",
                ))

            time.sleep(0.5)
        except Exception as e:
            pass

    print(f"  [Workday] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# Main entry point — called from scraper.py
# ═══════════════════════════════════════════════════════════

# Which Playwright scrapers to run (all enabled by default)
# LinkedIn + Indeed have their own script (run_scrape_browsers.py)
# with separate CSV output and Easy Apply detection.
PLAYWRIGHT_SCRAPERS = [
    ("Dice", scrape_dice),
    ("ZipRecruiter", scrape_ziprecruiter),
    ("SimplyHired", scrape_simplyhired),
    ("HealthECareers", scrape_health_ecareers),
]

# API scrapers (always safe to run)
API_SCRAPERS = [
    ("The Muse", scrape_themuse),
    ("Wellfound", scrape_wellfound),
    ("Workday", scrape_workday),
]

# Optional API scrapers (need keys)
OPTIONAL_API_SCRAPERS = [
    ("Google Jobs", scrape_google_jobs),
    ("Adzuna", scrape_adzuna),
]


def scrape_extended_sources(
    query: str,
    location: str = "",
    max_results: int = 25,
    use_playwright: bool = True,
) -> list[JobListing]:
    """Run all extended scrapers for a single query + location."""
    all_jobs = []

    # API scrapers (always run)
    for name, fn in API_SCRAPERS:
        if fn == scrape_workday:
            results = fn(query, location, max_results)
        elif fn == scrape_wellfound:
            results = fn(query, max_results)
        else:
            results = fn(query, location, max_results)
        all_jobs.extend(results)

    # Optional API scrapers (need env keys)
    for name, fn in OPTIONAL_API_SCRAPERS:
        results = fn(query, location, max_results)
        all_jobs.extend(results)

    # Playwright scrapers
    if use_playwright and HAS_PLAYWRIGHT:
        for name, fn in PLAYWRIGHT_SCRAPERS:
            results = fn(query, location, max_results)
            all_jobs.extend(results)
            time.sleep(1)

    return all_jobs


def cleanup():
    """Close the shared browser instance."""
    _close_browser()
