"""
Job Board Scraper — No AI, no HTML scraping.
Uses only free public JSON APIs.

Sources:
  1. Greenhouse API  — boards-api.greenhouse.io (no auth)
  2. Lever API       — api.lever.co (no auth)
  3. Himalayas API   — himalayas.app (no auth, best remote job API)
  4. RemoteOK API    — remoteok.com/api (no auth)
  5. USAJobs API     — data.usajobs.gov (free key, optional)
  6. Arbeitnow API   — arbeitnow.com (no auth)

LinkedIn/Indeed: generates search URLs for manual browsing (they block bots).

Usage:
    python scraper.py --profile alex
"""
import json
import re
import time
import hashlib
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

import requests

from config import ROLE_PROFILES, SEARCH_SETTINGS, DATA_DIR


@dataclass
class JobListing:
    title: str
    company: str
    location: str
    url: str
    source: str
    description: str = ""
    salary: str = ""
    date_posted: str = ""
    apply_method: str = ""
    job_id: str = ""
    role_hint: str = ""  # force-match to this role id (e.g. "ai-training")

    def __post_init__(self):
        if not self.job_id:
            raw = f"{self.title}-{self.company}-{self.source}"
            self.job_id = hashlib.md5(raw.encode()).hexdigest()[:12]


HEADERS = {
    "User-Agent": "JobHunterBot/1.0 (personal job search automation)",
    "Accept": "application/json",
}


# ═══════════════════════════════════════════════════════════
# Greenhouse (public JSON API, no auth)
# Add company slugs below. Find them on company career pages:
#   boards.greenhouse.io/stripe → slug is "stripe"
# ═══════════════════════════════════════════════════════════

GREENHOUSE_COMPANIES = [
    "eleanorhealth", "datadog", "cloudflare", "gitlab", "stripe",
    "figma", "notion", "airtable", "hashicorp", "hubspot",
    "duolingo", "reddit", "twilio", "okta", "zscaler",
    "crowdstrike", "paloaltonetworks", "mongodb", "elastic",
    "confluent", "snyk", "1password", "grafana",
]


def scrape_greenhouse(query: str, max_results: int = 25) -> list[JobListing]:
    jobs = []
    query_lower = query.lower()

    for slug in GREENHOUSE_COMPANIES:
        try:
            url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue

            for job in resp.json().get("jobs", []):
                title = job.get("title", "")
                if query_lower not in title.lower():
                    continue

                loc = job.get("location", {}).get("name", "") if job.get("location") else ""
                desc = re.sub(r"<[^>]+>", " ", job.get("content", ""))
                desc = re.sub(r"\s+", " ", desc).strip()

                jobs.append(JobListing(
                    title=title,
                    company=slug.replace("-", " ").title(),
                    location=loc,
                    url=job.get("absolute_url", ""),
                    source="Greenhouse",
                    description=desc[:1500],
                    date_posted=job.get("updated_at", ""),
                    apply_method="📋 Form Fill",
                ))
                if len(jobs) >= max_results:
                    return jobs

            time.sleep(0.3)
        except Exception as e:
            print(f"    [Greenhouse/{slug}] Error: {e}")

    print(f"  [Greenhouse] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# Lever (public JSON API, no auth)
# ═══════════════════════════════════════════════════════════

LEVER_COMPANIES = [
    "anthropic", "netlify", "postman", "webflow", "supabase",
    "vercel", "linear", "loom", "plaid", "anduril",
    "faire", "rippling", "ramp", "brex", "retool",
]


def scrape_lever(query: str, max_results: int = 25) -> list[JobListing]:
    jobs = []
    query_lower = query.lower()

    for slug in LEVER_COMPANIES:
        try:
            url = f"https://api.lever.co/v0/postings/{slug}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue

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
                        salary_range = f"{sal.get('min', '')} - {sal.get('max', '')}"

                jobs.append(JobListing(
                    title=title,
                    company=slug.replace("-", " ").title(),
                    location=loc,
                    salary=salary_range,
                    url=posting.get("hostedUrl", ""),
                    source="Lever",
                    description=posting.get("descriptionPlain", "")[:1500],
                    apply_method="📋 Form Fill",
                ))
                if len(jobs) >= max_results:
                    return jobs

            time.sleep(0.3)
        except Exception as e:
            print(f"    [Lever/{slug}] Error: {e}")

    print(f"  [Lever] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# Himalayas (free public JSON API, no auth)
# ═══════════════════════════════════════════════════════════

def scrape_himalayas(query: str, max_results: int = 25) -> list[JobListing]:
    jobs = []
    page = 1

    # Filter to US jobs at the API level (Himalayas supports country param)
    user_country = SEARCH_SETTINGS.get("locations", [])
    api_country = "United States"  # default to US
    for loc in user_country:
        if "united states" in loc.lower() or ", us" in loc.lower():
            api_country = "United States"
            break

    while len(jobs) < max_results:
        try:
            resp = requests.get(
                "https://himalayas.app/jobs/api/search",
                params={"q": query, "page": page, "sort": "recent",
                        "country": api_country},
                headers=HEADERS, timeout=15,
            )
            if resp.status_code != 200:
                break

            listings = resp.json().get("jobs", [])
            if not listings:
                break

            for job in listings:
                salary = ""
                if job.get("minSalary") and job.get("maxSalary"):
                    salary = f"${int(job['minSalary']):,} - ${int(job['maxSalary']):,}"

                loc_parts = job.get("locationRestrictions", [])
                location = ", ".join(loc_parts) if loc_parts else "Remote"

                jobs.append(JobListing(
                    title=job.get("title", ""),
                    company=job.get("companyName", ""),
                    location=location,
                    salary=salary,
                    url=f"https://himalayas.app/jobs/{job.get('slug', '')}",
                    source="Himalayas",
                    description=job.get("excerpt", "")[:1500],
                    date_posted=job.get("pubDate", ""),
                    apply_method="📎 Resume Upload",
                ))
                if len(jobs) >= max_results:
                    break

            page += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"    [Himalayas] Error: {e}")
            break

    print(f"  [Himalayas] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# RemoteOK (free JSON API, no auth)
# ═══════════════════════════════════════════════════════════

_remoteok_cache = None


def scrape_remoteok(query: str, max_results: int = 25) -> list[JobListing]:
    global _remoteok_cache
    jobs = []

    try:
        if _remoteok_cache is None:
            resp = requests.get("https://remoteok.com/api", headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                _remoteok_cache = resp.json()
            else:
                return jobs

        query_lower = query.lower()
        for item in _remoteok_cache:
            if not isinstance(item, dict) or "position" not in item:
                continue

            title = item.get("position", "")
            tags = " ".join(item.get("tags", []))
            desc = item.get("description", "")
            if query_lower not in f"{title} {tags} {desc}".lower():
                continue

            salary = ""
            if item.get("salary_min") and item.get("salary_max"):
                try:
                    salary = f"${int(item['salary_min']):,} - ${int(item['salary_max']):,}"
                except (ValueError, TypeError):
                    pass

            jobs.append(JobListing(
                title=title,
                company=item.get("company", ""),
                location="Remote",
                salary=salary,
                url=item.get("url", f"https://remoteok.com/remote-jobs/{item.get('id', '')}"),
                source="RemoteOK",
                description=desc[:1500],
                date_posted=item.get("date", ""),
                apply_method="📎 Resume Upload",
            ))
            if len(jobs) >= max_results:
                break
    except Exception as e:
        print(f"    [RemoteOK] Error: {e}")

    print(f"  [RemoteOK] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# USAJobs (free API, optional — needs free API key)
# Sign up: https://developer.usajobs.gov/
# ═══════════════════════════════════════════════════════════

def scrape_usajobs(query: str, location: str = "", max_results: int = 25) -> list[JobListing]:
    import os
    api_key = os.getenv("USAJOBS_API_KEY", "")
    api_email = os.getenv("USAJOBS_EMAIL", "")
    if not api_key or not api_email:
        return []

    jobs = []
    try:
        resp = requests.get(
            "https://data.usajobs.gov/api/search",
            params={
                "Keyword": query, "LocationName": location,
                "ResultsPerPage": min(max_results, 25),
                "SortField": "DatePosted", "SortDirection": "Desc",
            },
            headers={
                "Host": "data.usajobs.gov",
                "User-Agent": api_email,
                "Authorization-Key": api_key,
            },
            timeout=15,
        )
        if resp.status_code != 200:
            return jobs

        for item in resp.json().get("SearchResult", {}).get("SearchResultItems", []):
            m = item.get("MatchedObjectDescriptor", {})
            details = m.get("UserArea", {}).get("Details", {})

            salary = ""
            remuneration = m.get("PositionRemuneration", [])
            if remuneration:
                try:
                    s_min = remuneration[0].get("MinimumRange", "")
                    s_max = remuneration[0].get("MaximumRange", "")
                    if s_min and s_max:
                        salary = f"${float(s_min):,.0f} - ${float(s_max):,.0f}"
                except (ValueError, TypeError):
                    pass

            jobs.append(JobListing(
                title=m.get("PositionTitle", ""),
                company=m.get("OrganizationName", "US Government"),
                location=m.get("PositionLocationDisplay", ""),
                salary=salary,
                url=m.get("PositionURI", ""),
                source="USAJobs",
                description=details.get("JobSummary", "")[:1500],
                date_posted=m.get("PublicationStartDate", ""),
                apply_method="📋 Form Fill",
            ))
            if len(jobs) >= max_results:
                break
    except Exception as e:
        print(f"    [USAJobs] Error: {e}")

    print(f"  [USAJobs] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# Arbeitnow (free JSON API, no auth)
# ═══════════════════════════════════════════════════════════

def scrape_arbeitnow(query: str, max_results: int = 25) -> list[JobListing]:
    jobs = []
    page = 1

    while len(jobs) < max_results:
        try:
            resp = requests.get(
                f"https://www.arbeitnow.com/api/job-board-api?page={page}",
                headers=HEADERS, timeout=15,
            )
            if resp.status_code != 200:
                break

            data = resp.json()
            listings = data.get("data", [])
            if not listings:
                break

            query_lower = query.lower()
            for job in listings:
                title = job.get("title", "")
                desc = job.get("description", "")
                tags = " ".join(job.get("tags", []))
                if query_lower not in f"{title} {desc} {tags}".lower():
                    continue

                location = job.get("location", "")
                if job.get("remote", False):
                    location = f"Remote — {location}" if location else "Remote"

                jobs.append(JobListing(
                    title=title,
                    company=job.get("company_name", ""),
                    location=location,
                    url=job.get("url", ""),
                    source="Arbeitnow",
                    description=desc[:1500],
                    date_posted=job.get("created_at", ""),
                    apply_method="📎 Resume Upload",
                ))
                if len(jobs) >= max_results:
                    break

            if not data.get("links", {}).get("next"):
                break
            page += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"    [Arbeitnow] Error: {e}")
            break

    print(f"  [Arbeitnow] {len(jobs)} jobs for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# LinkedIn / Indeed URL generator (manual browsing)
# ═══════════════════════════════════════════════════════════

def generate_manual_urls(query: str, location: str = "") -> list[dict]:
    urls = []

    li_params = f"keywords={requests.utils.quote(query)}"
    if location:
        li_params += f"&location={requests.utils.quote(location)}"
    li_params += "&f_TPR=r604800&f_AL=true&sortBy=DD"
    urls.append({
        "title": f"LinkedIn Easy Apply: {query}",
        "url": f"https://www.linkedin.com/jobs/search/?{li_params}",
        "source": "LinkedIn (manual)",
    })

    indeed_params = f"q={requests.utils.quote(query)}"
    if location:
        indeed_params += f"&l={requests.utils.quote(location)}"
    indeed_params += "&sort=date&fromage=7"
    urls.append({
        "title": f"Indeed: {query}",
        "url": f"https://www.indeed.com/jobs?{indeed_params}",
        "source": "Indeed (manual)",
    })

    return urls


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

def scrape_all_jobs() -> list[JobListing]:
    all_jobs = []
    seen_ids = set()
    locations = SEARCH_SETTINGS.get("locations", ["Remote"])
    max_per = SEARCH_SETTINGS.get("max_results_per_query", 25)

    # Import extended scrapers
    try:
        from scraper_extended import scrape_extended_sources, cleanup as ext_cleanup
        has_extended = True
    except ImportError:
        has_extended = False

    for role_id, profile in ROLE_PROFILES.items():
        print(f"\n{'='*60}")
        print(f"  Scraping: {profile['label']}")
        print(f"  Salary: ${profile.get('salary_min',0):,} – ${profile.get('salary_max',0):,}")
        print(f"{'='*60}")

        for query in profile["search_queries"]:
            # Original API scrapers
            for fn in [scrape_himalayas, scrape_remoteok,
                       scrape_greenhouse, scrape_lever, scrape_arbeitnow]:
                for j in fn(query, max_per):
                    if j.job_id not in seen_ids:
                        seen_ids.add(j.job_id)
                        all_jobs.append(j)

            # USAJobs (location-specific)
            for loc in locations:
                if loc.lower() != "remote":
                    for j in scrape_usajobs(query, loc, max_per):
                        if j.job_id not in seen_ids:
                            seen_ids.add(j.job_id)
                            all_jobs.append(j)

            # Extended scrapers (Workday, The Muse, Wellfound, Adzuna, Google Jobs)
            if has_extended:
                for loc in locations:
                    for j in scrape_extended_sources(query, loc, max_per, use_playwright=False):
                        if j.job_id not in seen_ids:
                            seen_ids.add(j.job_id)
                            all_jobs.append(j)

            time.sleep(0.5)

    # Cleanup extended browser if used
    if has_extended:
        try:
            ext_cleanup()
        except Exception:
            pass

    # Save
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output = DATA_DIR / f"raw_jobs_{timestamp}.json"
    with open(output, "w") as f:
        json.dump([asdict(j) for j in all_jobs], f, indent=2)

    # Summary
    sources = {}
    for j in all_jobs:
        sources[j.source] = sources.get(j.source, 0) + 1

    print(f"\n{'='*60}")
    print(f"  Total: {len(all_jobs)} unique jobs")
    for src, c in sorted(sources.items(), key=lambda x: x[1], reverse=True):
        print(f"    {src}: {c}")
    print(f"  Saved: {output}")
    print(f"{'='*60}")

    return all_jobs


if __name__ == "__main__":
    scrape_all_jobs()
