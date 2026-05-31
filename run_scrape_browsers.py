"""
Phase 1B: Scrape LinkedIn + Indeed with Playwright.

Outputs to a SEPARATE CSV: output/{profile}/browser_jobs.csv
This CSV is informational only — no auto-apply for these jobs.
Shows whether Easy Apply / Quick Apply is available and direct apply links.

Usage:
    python run_scrape_browsers.py --profile alex
    python run_scrape_browsers.py --profile marcelli
"""
import csv
import time
import re
import argparse
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

import requests

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

from config import (
    ROLE_PROFILES, SEARCH_SETTINGS, PROFILE_DIR, DATA_DIR,
    LOCATION_FILTER, ACTIVE_PROFILE_NAME,
)


BROWSER_CSV = PROFILE_DIR / "browser_jobs.csv"

BROWSER_COLUMNS = [
    "Job Title",
    "Company",
    "Location",
    "Work Type",
    "Salary",
    "Role Category",
    "Source",
    "Easy Apply",
    "Direct Apply Link",
    "Job URL",
    "Date Found",
    "Apply",
    "Notes",
]


@dataclass
class BrowserJob:
    title: str
    company: str
    location: str
    work_type: str
    salary: str
    role_category: str
    source: str
    easy_apply: str  # "Yes", "No", "Unknown"
    direct_apply_link: str
    job_url: str


def _detect_work_type_simple(location: str, title: str) -> str:
    combined = f"{location} {title}".lower()
    if re.search(r'\bhybrid\b', combined):
        return "Hybrid"
    if re.search(r'\bremote\b', combined):
        return "Remote"
    if re.search(r'\bon[- ]?site\b|\bin[- ]?office\b', combined):
        return "On-site"
    if location.strip():
        return "On-site"
    return "Unknown"


def _is_location_match(location: str) -> bool:
    """Check if job location matches our filter (Remote or nearby)."""
    loc_lower = location.lower()

    if LOCATION_FILTER.get("include_remote", True) and "remote" in loc_lower:
        return True

    city = LOCATION_FILTER.get("city", "").lower()
    state = LOCATION_FILTER.get("state", "").lower()
    nearby = [c.lower() for c in LOCATION_FILTER.get("nearby_cities", [])]

    if city and city in loc_lower:
        return True
    if state and re.search(r'\b' + re.escape(state) + r'\b', loc_lower):
        return True
    for c in nearby:
        if c in loc_lower:
            return True

    return False


def scrape_linkedin_jobs(query: str, location: str, max_results: int, page) -> list[BrowserJob]:
    """Scrape LinkedIn public job listings."""
    jobs = []
    try:
        params = f"keywords={requests.utils.quote(query)}&f_TPR=r604800&sortBy=DD"
        if location:
            params += f"&location={requests.utils.quote(location)}"
        url = f"https://www.linkedin.com/jobs/search/?{params}"

        page.goto(url, timeout=25000)
        page.wait_for_timeout(4000)

        # Scroll to load
        for _ in range(3):
            page.evaluate("window.scrollBy(0, 800)")
            page.wait_for_timeout(1000)

        cards = page.query_selector_all("div.base-card, div.job-search-card")
        for card in cards[:max_results]:
            try:
                title_el = card.query_selector("h3.base-search-card__title")
                company_el = card.query_selector("h4.base-search-card__subtitle")
                location_el = card.query_selector("span.job-search-card__location")
                link_el = card.query_selector("a.base-card__full-link")
                salary_el = card.query_selector("span.job-search-card__salary-info")

                title = (title_el.inner_text() or "").strip() if title_el else ""
                if not title:
                    continue

                loc = (location_el.inner_text() or "").strip() if location_el else ""
                href = (link_el.get_attribute("href") or "").split("?")[0] if link_el else ""

                # LinkedIn Easy Apply detection from the listing card
                easy_apply_badge = card.query_selector("[class*='easy-apply'], [class*='EasyApply']")
                easy_apply = "Yes" if easy_apply_badge else "Check"

                jobs.append(BrowserJob(
                    title=title,
                    company=(company_el.inner_text() or "").strip() if company_el else "Unknown",
                    location=loc,
                    work_type=_detect_work_type_simple(loc, title),
                    salary=(salary_el.inner_text() or "").strip() if salary_el else "",
                    role_category="",
                    source="LinkedIn",
                    easy_apply=easy_apply,
                    direct_apply_link=href,
                    job_url=href,
                ))
            except Exception:
                continue

    except Exception as e:
        print(f"    [LinkedIn] Error: {e}")

    print(f"  [LinkedIn] {len(jobs)} jobs for '{query}'")
    return jobs


def scrape_indeed_jobs(query: str, location: str, max_results: int, page) -> list[BrowserJob]:
    """Scrape Indeed job listings with Easy Apply detection."""
    jobs = []
    try:
        params = f"q={requests.utils.quote(query)}&sort=date&fromage=7"
        if location:
            params += f"&l={requests.utils.quote(location)}"
        url = f"https://www.indeed.com/jobs?{params}"

        page.goto(url, timeout=25000)
        page.wait_for_timeout(4000)

        cards = page.query_selector_all("div.job_seen_beacon, div.jobsearch-ResultsList > div[data-jk]")
        for card in cards[:max_results]:
            try:
                title_el = card.query_selector("h2.jobTitle a, h2.jobTitle span")
                company_el = card.query_selector("[data-testid='company-name'], span.companyName")
                location_el = card.query_selector("[data-testid='text-location'], div.companyLocation")
                salary_el = card.query_selector("div.salary-snippet-container, div.metadata.salary-snippet-container")
                link_el = card.query_selector("h2.jobTitle a, a.jcs-JobTitle")

                title = (title_el.inner_text() or "").strip() if title_el else ""
                if not title:
                    continue

                loc = (location_el.inner_text() or "").strip() if location_el else ""

                href = ""
                if link_el:
                    href = link_el.get_attribute("href") or ""
                    if href.startswith("/"):
                        href = f"https://www.indeed.com{href}"

                # Indeed Easy Apply / "Apply now" detection
                easy_badge = card.query_selector(
                    "[class*='iaLabel'], [aria-label*='easily apply'], "
                    "[class*='EasyApply'], span.ialbl"
                )
                easy_apply = "Yes" if easy_badge else "No"

                jobs.append(BrowserJob(
                    title=title,
                    company=(company_el.inner_text() or "").strip() if company_el else "Unknown",
                    location=loc,
                    work_type=_detect_work_type_simple(loc, title),
                    salary=(salary_el.inner_text() or "").strip() if salary_el else "",
                    role_category="",
                    source="Indeed",
                    easy_apply=easy_apply,
                    direct_apply_link=href,
                    job_url=href,
                ))
            except Exception:
                continue

    except Exception as e:
        print(f"    [Indeed] Error: {e}")

    print(f"  [Indeed] {len(jobs)} jobs for '{query}'")
    return jobs


def _check_redirect_apply(job_url: str, page) -> str:
    """Visit a job URL and check if it has a direct apply button/link."""
    if not job_url:
        return ""
    try:
        page.goto(job_url, timeout=15000)
        page.wait_for_timeout(2000)

        # Look for apply buttons that link somewhere
        apply_btn = page.query_selector(
            "a[href*='apply'], button[class*='apply'], "
            "a[class*='apply'], [data-testid*='apply'] a"
        )
        if apply_btn:
            href = apply_btn.get_attribute("href") or ""
            if href and href.startswith("http"):
                return href
    except Exception:
        pass
    return ""


def run_browser_scrape():
    if not HAS_PLAYWRIGHT:
        print("  ❌ Playwright not installed. Run: pip install playwright && playwright install chromium")
        return

    print(f"\n🌐 Browser Scrape: LinkedIn + Indeed")
    print(f"{'='*60}")
    print(f"  Output: {BROWSER_CSV}")
    print(f"  (No auto-apply — informational only)\n")

    locations = SEARCH_SETTINGS.get("locations", ["Remote"])
    max_per = SEARCH_SETTINGS.get("max_results_per_query", 25)

    all_jobs: list[BrowserJob] = []
    seen = set()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()

        for role_id, profile in ROLE_PROFILES.items():
            print(f"\n  ── {profile['label']} ──")

            for query in profile["search_queries"]:
                for loc in locations:
                    # LinkedIn
                    li_jobs = scrape_linkedin_jobs(query, loc, max_per, page)
                    for j in li_jobs:
                        key = f"{j.title}-{j.company}-{j.source}"
                        if key not in seen:
                            seen.add(key)
                            j.role_category = profile["label"]
                            all_jobs.append(j)
                    time.sleep(2)

                    # Indeed
                    indeed_jobs = scrape_indeed_jobs(query, loc, max_per, page)
                    for j in indeed_jobs:
                        key = f"{j.title}-{j.company}-{j.source}"
                        if key not in seen:
                            seen.add(key)
                            j.role_category = profile["label"]
                            all_jobs.append(j)
                    time.sleep(2)

        # Filter by location
        filtered = [j for j in all_jobs if _is_location_match(j.location)]
        dropped = len(all_jobs) - len(filtered)

        # Optionally check first 10 jobs for direct apply links
        print(f"\n  Checking direct apply links (first 20 jobs)...")
        for j in filtered[:20]:
            if j.easy_apply == "Yes" and j.job_url:
                link = _check_redirect_apply(j.job_url, page)
                if link:
                    j.direct_apply_link = link
            time.sleep(0.5)

        browser.close()

    # Write CSV
    today = datetime.now().strftime("%Y-%m-%d")
    with open(BROWSER_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=BROWSER_COLUMNS)
        writer.writeheader()
        for j in filtered:
            writer.writerow({
                "Job Title": j.title,
                "Company": j.company,
                "Location": j.location,
                "Work Type": j.work_type,
                "Salary": j.salary,
                "Role Category": j.role_category,
                "Source": j.source,
                "Easy Apply": j.easy_apply,
                "Direct Apply Link": j.direct_apply_link,
                "Job URL": j.job_url,
                "Date Found": today,
                "Apply": "",
                "Notes": "",
            })

    print(f"\n{'='*60}")
    print(f"  ✅ {len(filtered)} jobs saved to {BROWSER_CSV}")
    if dropped:
        print(f"  ⏭️  Skipped {dropped} jobs (not Remote or near {LOCATION_FILTER['city']})")

    sources = {}
    for j in filtered:
        sources[j.source] = sources.get(j.source, 0) + 1
    for src, c in sorted(sources.items(), key=lambda x: -x[1]):
        print(f"    {src}: {c}")

    easy_count = sum(1 for j in filtered if j.easy_apply == "Yes")
    print(f"  ⚡ Easy Apply available: {easy_count}")
    print(f"\n  📄 Open: {BROWSER_CSV}")
    print(f"  (No auto-apply — review and apply manually)")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="Profile to use")
    args = parser.parse_args()
    run_browser_scrape()
