"""
Web Search Scraper — Finds jobs across the entire internet, not just job boards.

Two strategies:
  1. Google search for job postings matching role queries + location
  2. Company career page discovery — find companies in the user's area,
     then check their Greenhouse/Lever/Workday career pages

Requires: SERPAPI_KEY in .env (for Google search) OR uses free DuckDuckGo fallback.

Usage:
    Called from run_scrape.py via scrape_web_sources()
    Or standalone: python scraper_web.py --profile yourname
"""
import json
import os
import re
import time
import hashlib
from datetime import datetime
from pathlib import Path

import requests

from scraper import JobListing, HEADERS

# ═══════════════════════════════════════════════════════════
# Company Database — Companies with known career page patterns
#
# Add companies you want to track. Group by ATS type.
# The scraper checks each company's career API for matching jobs.
# ═══════════════════════════════════════════════════════════

# Companies on Greenhouse (boards-api.greenhouse.io)
GREENHOUSE_COMPANIES_EXTRA = [
    # Tech
    "airbnb", "coinbase", "doordash", "dropbox", "lyft", "palantir",
    "pinterest", "robinhood", "shopify", "snap", "spotify", "square",
    "uber", "zoom", "atlassian", "canva", "databricks", "dbt-labs",
    "fastly", "gusto", "intercom", "lemonade", "miro", "pagerduty",
    "samsara", "segment", "sentry", "toast", "vanta", "verkada",
    # Finance/Insurance
    "chime", "marqeta", "sofi", "upstart", "wealthfront",
    # Healthcare
    "cityblock", "flatiron", "oscar", "tempus", "veracyte",
]

# Companies on Lever (api.lever.co)
LEVER_COMPANIES_EXTRA = [
    "airtable", "anduril", "brex", "cockroachlabs", "dbt-labs",
    "faire", "figma", "linear", "loom", "notion", "plaid",
    "postman", "ramp", "retool", "rippling", "supabase",
    "vercel", "webflow",
]

# Companies with known Workday career sites
# Format: (company_name, workday_tenant_url)
WORKDAY_COMPANIES = [
    ("Amazon", "https://www.amazon.jobs/en/search"),
    ("Microsoft", "https://careers.microsoft.com/us/en/search-results"),
    ("Google", "https://www.google.com/about/careers/applications/jobs/results"),
    ("Meta", "https://www.metacareers.com/jobs"),
    ("Apple", "https://jobs.apple.com/en-us/search"),
    ("Salesforce", "https://careers.salesforce.com/en/jobs"),
    ("Oracle", "https://careers.oracle.com/jobs"),
    ("IBM", "https://careers.ibm.com/job/search"),
    ("Cisco", "https://jobs.cisco.com/jobs/SearchJobs"),
    ("Adobe", "https://careers.adobe.com/us/en/search-results"),
    ("SAP", "https://jobs.sap.com/search"),
    ("VMware", "https://careers.vmware.com/main/jobs"),
    ("Intuit", "https://jobs.intuit.com/search-jobs"),
    ("ServiceNow", "https://careers.servicenow.com/jobs/search"),
    ("Snowflake", "https://careers.snowflake.com/us/en/search-results"),
]

# Direct career page URLs to check (generic pattern)
# These get searched via Google/DuckDuckGo
CAREER_PAGE_PATTERNS = [
    'site:greenhouse.io "{query}"',
    'site:lever.co "{query}"',
    'site:jobs.lever.co "{query}"',
    'site:myworkdayjobs.com "{query}"',
    'site:careers.* "{query}" {location}',
    '"{query}" "apply now" {location} job',
    '"{query}" hiring {location} salary',
    '"{query}" career opportunity {location}',
]


# ═══════════════════════════════════════════════════════════
# DuckDuckGo Search (free, no API key)
# ═══════════════════════════════════════════════════════════

def _search_duckduckgo(query: str, max_results: int = 20) -> list[dict]:
    """Search DuckDuckGo and return result URLs + titles."""
    results = []
    try:
        # DuckDuckGo HTML endpoint (no API key needed)
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                              "AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return results

        # Parse results from HTML (simple regex — no BS4 dependency)
        # DuckDuckGo wraps results in <a class="result__a" href="...">
        links = re.findall(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            resp.text, re.DOTALL,
        )
        for url, title_html in links[:max_results]:
            # Clean URL (DuckDuckGo sometimes wraps in redirect)
            if "duckduckgo.com" in url:
                url_match = re.search(r'uddg=([^&]+)', url)
                if url_match:
                    from urllib.parse import unquote
                    url = unquote(url_match.group(1))

            title = re.sub(r'<[^>]+>', '', title_html).strip()
            if url and title:
                results.append({"url": url, "title": title})

    except Exception as e:
        print(f"    [DuckDuckGo] Error: {e}")

    return results


# ═══════════════════════════════════════════════════════════
# SerpAPI Google Search (paid, richer results)
# ═══════════════════════════════════════════════════════════

def _search_google_serpapi(query: str, max_results: int = 20) -> list[dict]:
    """Search Google via SerpAPI. Returns job-like results."""
    api_key = os.getenv("SERPAPI_KEY", "")
    if not api_key:
        return []

    results = []
    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={
                "q": query,
                "api_key": api_key,
                "num": min(max_results, 20),
                "engine": "google",
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return results

        data = resp.json()

        # Regular search results
        for r in data.get("organic_results", []):
            results.append({
                "url": r.get("link", ""),
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
            })

        # Google Jobs widget results (bonus)
        for j in data.get("jobs_results", []):
            results.append({
                "url": j.get("apply_link", j.get("link", "")),
                "title": j.get("title", ""),
                "company": j.get("company_name", ""),
                "location": j.get("location", ""),
                "snippet": j.get("description", ""),
                "is_google_job": True,
            })

    except Exception as e:
        print(f"    [SerpAPI] Error: {e}")

    return results


# ═══════════════════════════════════════════════════════════
# Career Page Scrapers — Check company APIs directly
# ═══════════════════════════════════════════════════════════

def _scrape_greenhouse_company(slug: str, query: str, max_results: int = 10) -> list[JobListing]:
    """Check a single Greenhouse company for matching jobs."""
    jobs = []
    query_lower = query.lower()
    try:
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return jobs

        for job in resp.json().get("jobs", []):
            title = job.get("title", "")
            if query_lower not in title.lower():
                continue

            loc = job.get("location", {}).get("name", "") if job.get("location") else ""
            jobs.append(JobListing(
                title=title,
                company=slug.replace("-", " ").title(),
                location=loc,
                url=job.get("absolute_url", ""),
                source="Web Search (Greenhouse)",
                description="",
                apply_method="📋 Form Fill",
            ))
            if len(jobs) >= max_results:
                break
    except Exception:
        pass
    return jobs


def _scrape_lever_company(slug: str, query: str, max_results: int = 10) -> list[JobListing]:
    """Check a single Lever company for matching jobs."""
    jobs = []
    query_lower = query.lower()
    try:
        url = f"https://api.lever.co/v0/postings/{slug}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return jobs

        for posting in resp.json():
            title = posting.get("text", "")
            if query_lower not in title.lower():
                continue

            loc = posting.get("categories", {}).get("location", "") if posting.get("categories") else ""
            salary_range = ""
            sal = posting.get("salaryRange", {})
            if sal:
                try:
                    s_min, s_max = sal.get("min", ""), sal.get("max", "")
                    if s_min and s_max:
                        salary_range = f"${int(s_min):,} - ${int(s_max):,}"
                except (ValueError, TypeError):
                    pass

            jobs.append(JobListing(
                title=title,
                company=slug.replace("-", " ").title(),
                location=loc,
                salary=salary_range,
                url=posting.get("hostedUrl", ""),
                source="Web Search (Lever)",
                description=posting.get("descriptionPlain", "")[:500],
                apply_method="📋 Form Fill",
            ))
            if len(jobs) >= max_results:
                break
    except Exception:
        pass
    return jobs


# ═══════════════════════════════════════════════════════════
# Web Search Result → JobListing converter
# ═══════════════════════════════════════════════════════════

def _is_job_url(url: str) -> bool:
    """Check if a URL looks like a job posting (not a blog, news article, etc.)."""
    job_patterns = [
        r"greenhouse\.io/", r"lever\.co/", r"myworkdayjobs\.com/",
        r"/jobs?/", r"/careers?/", r"/positions?/", r"/openings?/",
        r"/apply", r"job[-_]?id", r"/posting/",
        r"indeed\.com/viewjob", r"linkedin\.com/jobs/view",
        r"glassdoor\.com/job-listing",
    ]
    url_lower = url.lower()
    return any(re.search(p, url_lower) for p in job_patterns)


def _extract_company_from_url(url: str) -> str:
    """Try to extract company name from a career page URL."""
    # greenhouse.io/companyname or boards.greenhouse.io/companyname
    m = re.search(r'greenhouse\.io/(\w+)', url)
    if m:
        return m.group(1).replace("-", " ").title()

    m = re.search(r'lever\.co/(\w+)', url)
    if m:
        return m.group(1).replace("-", " ").title()

    # Generic career domain: careers.companyname.com
    m = re.search(r'careers?\.(\w+)\.\w+', url)
    if m:
        return m.group(1).title()

    # jobs.companyname.com
    m = re.search(r'jobs\.(\w+)\.\w+', url)
    if m:
        return m.group(1).title()

    return ""


def _search_result_to_job(result: dict, query: str) -> JobListing | None:
    """Convert a web search result to a JobListing if it looks like a job."""
    url = result.get("url", "")
    title = result.get("title", "")

    if not url or not title:
        return None

    # Google Jobs results are already structured
    if result.get("is_google_job"):
        return JobListing(
            title=title,
            company=result.get("company", ""),
            location=result.get("location", ""),
            url=url,
            source="Web Search (Google Jobs)",
            description=result.get("snippet", "")[:500],
            apply_method="✍️ Manual",
        )

    # Only keep URLs that look like job postings
    if not _is_job_url(url):
        return None

    company = _extract_company_from_url(url)

    return JobListing(
        title=title,
        company=company,
        location="",
        url=url,
        source="Web Search",
        description=result.get("snippet", "")[:500],
        apply_method="✍️ Manual",
    )


# ═══════════════════════════════════════════════════════════
# Main entry point
# ═══════════════════════════════════════════════════════════

def scrape_web_sources(
    queries: list[str],
    location: str,
    max_results: int = 25,
    company_slugs_greenhouse: list[str] | None = None,
    company_slugs_lever: list[str] | None = None,
) -> list[JobListing]:
    """
    Search the broader internet for jobs matching the given queries.

    Strategy:
    1. Google/DuckDuckGo search for job postings
    2. Check extra company career pages on Greenhouse/Lever

    Returns list of JobListing objects.
    """
    all_jobs = []
    seen_urls = set()
    has_serpapi = bool(os.getenv("SERPAPI_KEY", ""))

    print(f"\n  🌐 Web Search — scanning internet for jobs...")
    print(f"     Engine: {'Google (SerpAPI)' if has_serpapi else 'DuckDuckGo (free)'}")

    # ── Strategy 1: Web search for job postings ──────────
    for query in queries:
        search_queries = [
            f'"{query}" job opening {location}',
            f'"{query}" hiring {location} apply',
            f'site:greenhouse.io OR site:lever.co "{query}" {location}',
        ]

        for sq in search_queries:
            if has_serpapi:
                results = _search_google_serpapi(sq, max_results=10)
            else:
                results = _search_duckduckgo(sq, max_results=10)

            for r in results:
                job = _search_result_to_job(r, query)
                if job and job.url not in seen_urls:
                    seen_urls.add(job.url)
                    all_jobs.append(job)

            time.sleep(1.0)  # Rate limit

    web_count = len(all_jobs)
    print(f"     Web search: {web_count} job URLs found")

    # ── Strategy 2: Check extra company career pages ─────
    gh_slugs = company_slugs_greenhouse or GREENHOUSE_COMPANIES_EXTRA
    lv_slugs = company_slugs_lever or LEVER_COMPANIES_EXTRA

    company_jobs = 0
    for query in queries:
        # Greenhouse companies
        for slug in gh_slugs:
            for job in _scrape_greenhouse_company(slug, query, max_results=5):
                if job.url not in seen_urls:
                    seen_urls.add(job.url)
                    all_jobs.append(job)
                    company_jobs += 1
            time.sleep(0.2)

        # Lever companies
        for slug in lv_slugs:
            for job in _scrape_lever_company(slug, query, max_results=5):
                if job.url not in seen_urls:
                    seen_urls.add(job.url)
                    all_jobs.append(job)
                    company_jobs += 1
            time.sleep(0.2)

    print(f"     Company career pages: {company_jobs} jobs from {len(gh_slugs) + len(lv_slugs)} companies")
    print(f"     Total web search: {len(all_jobs)} unique jobs")

    return all_jobs[:max_results]


def cleanup():
    """No browser to clean up — web search uses HTTP only."""
    pass


# ═══════════════════════════════════════════════════════════
# Standalone mode
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    from config import ROLE_PROFILES, SEARCH_SETTINGS

    parser = argparse.ArgumentParser(description="Web search for jobs")
    parser.add_argument("--profile", help="Profile to use")
    parser.add_argument("--query", help="Single search query (overrides profile)")
    parser.add_argument("--location", default="Remote", help="Location filter")
    args = parser.parse_args()

    if args.query:
        queries = [args.query]
    else:
        queries = []
        for role in ROLE_PROFILES.values():
            queries.extend(role["search_queries"])

    locations = SEARCH_SETTINGS.get("locations", ["Remote"])
    location = args.location or (locations[0] if locations else "Remote")

    jobs = scrape_web_sources(queries, location, max_results=50)

    print(f"\n{'='*60}")
    for j in jobs[:20]:
        print(f"  {j.title} @ {j.company or '?'}")
        print(f"    {j.url}")
        print(f"    Source: {j.source}")
    print(f"{'='*60}")
    print(f"  Total: {len(jobs)} jobs")
