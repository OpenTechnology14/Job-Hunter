"""
Freelance Board Scraper — part-time / contract gigs.

Feeds roles that carry `"freelance_boards": True` in ROLE_PROFILES
(e.g. the it-automation-contractor role). Two mechanisms:

1. Freelancer.com public API (no auth) — real project listings.
   Hourly projects are filtered to the role's max_hours_per_week
   commitment when the poster specified one; fixed-price projects pass
   through (one-off builds fit a ≤10 hrs/week schedule by nature).

2. Manual search rows for boards that block bots (Upwork, PeoplePerHour,
   Guru, Braintrust). Each becomes ONE row in jobs.csv with a prebuilt
   part-time-filtered search URL — click it, browse, apply manually.
   URL-based dedupe in local_sync means these are written once, not
   re-added every run.

All rows carry role_hint=<role_id> so the matcher force-assigns the
role (freelance project titles like "Fix my Google Sheets sync" would
never keyword-match otherwise).

Usage:
    Called from run_scrape.py (Step 1d)
    python scraper_freelance.py --profile alex     # standalone test
"""
import re
import time

import requests


HEADERS = {
    "User-Agent": "JobHunterBot/1.0 (personal job search automation)",
    "Accept": "application/json",
}


# ═══════════════════════════════════════════════════════════
# Freelancer.com (free public JSON API, no auth)
# ═══════════════════════════════════════════════════════════

def scrape_freelancer_com(query: str, max_results: int = 25,
                          max_hours: int = 0) -> list:
    """Search active Freelancer.com projects.

    max_hours > 0 drops hourly projects whose stated weekly commitment
    exceeds it. Projects with no stated commitment pass through for
    manual review (same philosophy as the no-salary-listed rule).
    """
    from scraper import JobListing
    jobs = []
    try:
        resp = requests.get(
            "https://www.freelancer.com/api/projects/0.1/projects/active/",
            params={
                "query": query,
                "limit": min(max_results * 2, 50),  # headroom for hour-filtering
                "compact": "true",
                "full_description": "false",
                "sort_field": "time_updated",
            },
            headers=HEADERS, timeout=15,
        )
        if resp.status_code != 200:
            print(f"    [Freelancer.com] HTTP {resp.status_code} for '{query}'")
            return jobs

        # Freelancer's query param matches very loosely (a search for
        # "IT Automation" returns game mods and dropshipping gigs), so
        # require a significant query word to actually appear in the
        # title or description. Words under 3 chars ("IT") are skipped —
        # as substrings they match almost anything.
        tokens = [w for w in query.lower().split() if len(w) >= 3]
        token_re = re.compile(
            r"\b(?:" + "|".join(re.escape(t) for t in tokens) + r")",
            re.IGNORECASE,
        ) if tokens else None

        for proj in resp.json().get("result", {}).get("projects", []):
            title = proj.get("title", "")
            if not title:
                continue

            if token_re and not token_re.search(
                    f"{title} {proj.get('preview_description') or ''}"):
                continue

            ptype = proj.get("type", "")  # "hourly" | "fixed"

            # Weekly-hours cap: only enforceable when the poster set one
            hours_note = ""
            if ptype == "hourly":
                commitment = (proj.get("hourly_project_info") or {}).get("commitment") or {}
                hours = commitment.get("hours")
                interval = (commitment.get("interval") or "").lower()
                if hours and "week" in interval:
                    if max_hours and hours > max_hours:
                        continue
                    hours_note = f" · {hours} hrs/wk"

            budget = proj.get("budget") or {}
            currency = (proj.get("currency") or {}).get("sign", "$")
            b_min, b_max = budget.get("minimum"), budget.get("maximum")
            salary = ""
            if b_min and b_max:
                salary = f"{currency}{b_min:,.0f} - {currency}{b_max:,.0f}"
            elif b_min:
                salary = f"{currency}{b_min:,.0f}+"
            if salary and ptype == "hourly":
                salary += "/hr"

            seo_url = proj.get("seo_url", "")
            jobs.append(JobListing(
                title=title,
                company=f"Freelancer.com ({ptype or 'project'}){hours_note}",
                location="Remote",
                salary=salary,
                url=f"https://www.freelancer.com/projects/{seo_url}" if seo_url else "",
                source="Freelancer.com",
                description=(proj.get("preview_description") or "")[:1500],
                apply_method="✍️ Manual",
            ))
            if len(jobs) >= max_results:
                break
    except Exception as e:
        print(f"    [Freelancer.com] Error: {e}")

    print(f"  [Freelancer.com] {len(jobs)} projects for '{query}'")
    return jobs


# ═══════════════════════════════════════════════════════════
# Manual search rows — boards that block automated scraping.
# One stable-URL row per board; dedupe keeps them from repeating.
# ═══════════════════════════════════════════════════════════

def _q(text: str) -> str:
    return requests.utils.quote(text)


def freelance_manual_search_rows(query: str) -> list:
    """Prebuilt part-time-filtered search links for bot-blocked boards."""
    from scraper import JobListing

    boards = [
        (
            "Upwork",
            # workload filter = "as needed" + "part time" (<30 hrs/wk)
            f"https://www.upwork.com/nx/search/jobs/?q={_q(query)}"
            "&workload=as_needed,part_time&sort=recency",
            "Hourly + fixed-price gigs; strongest demand for automation scripts",
        ),
        (
            "PeoplePerHour",
            f"https://www.peopleperhour.com/freelance-jobs?q={_q(query)}",
            "Smaller projects, often one-off — good ≤10 hr/wk fits",
        ),
        (
            "Guru",
            f"https://www.guru.com/d/jobs/q/{_q(query)}/",
            "IT & automation category has steady small contracts",
        ),
        (
            "Braintrust",
            f"https://app.usebraintrust.com/jobs/?search={_q(query)}",
            "Vetted network, 0% freelancer fee; some part-time contracts",
        ),
    ]

    rows = []
    for name, url, note in boards:
        rows.append(JobListing(
            title=f"🔎 {name} search: {query}",
            company=f"{name} (manual search)",
            location="Remote",
            url=url,
            source=f"{name}",
            description=f"Saved part-time search on {name}. {note}. "
                        "Open the link, browse current gigs, apply on-platform.",
            apply_method="✍️ Manual",
        ))
    return rows


# ═══════════════════════════════════════════════════════════
# Entry point — called from run_scrape.py Step 1d
# ═══════════════════════════════════════════════════════════

def scrape_freelance_sources(queries: list, role_id: str,
                             max_hours: int = 0,
                             max_results: int = 25) -> list:
    """Run all freelance sources for one role's queries."""
    all_jobs = []
    seen = set()

    for query in queries:
        for j in scrape_freelancer_com(query, max_results, max_hours):
            j.role_hint = role_id
            if j.job_id not in seen:
                seen.add(j.job_id)
                all_jobs.append(j)
        time.sleep(0.5)

    # One set of manual search rows per role, built from the first two
    # queries (one row per board per query keeps the sheet tidy).
    for query in queries[:2]:
        for j in freelance_manual_search_rows(query):
            j.role_hint = role_id
            if j.job_id not in seen:
                seen.add(j.job_id)
                all_jobs.append(j)

    print(f"  💼 Freelance sources: {len(all_jobs)} rows for role '{role_id}'")
    return all_jobs


if __name__ == "__main__":
    import argparse
    from config import ROLE_PROFILES

    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="Profile to use")
    args = parser.parse_args()

    found = False
    for rid, role in ROLE_PROFILES.items():
        if not role.get("freelance_boards"):
            continue
        found = True
        print(f"\n💼 Freelance test for role '{rid}' "
              f"(max {role.get('max_hours_per_week', 0) or '∞'} hrs/wk)")
        jobs = scrape_freelance_sources(
            role["search_queries"][:3], rid,
            max_hours=role.get("max_hours_per_week", 0),
            max_results=10,
        )
        for j in jobs[:20]:
            print(f"    [{j.source}] {j.title[:60]}  {j.salary}")

    if not found:
        print("No role in this profile has \"freelance_boards\": True")
