"""
Boolean & X-Ray Search — build the advanced search queries the job
platforms' native search understands, and (unlike a copy-paste string
builder) actually RUN the X-Ray queries to pull real postings into the
pipeline.

Two things live here:

1. QUERY BUILDER
   Turns a role's terms into a Boolean string:
     ("IT Consultant" OR "Automation Consultant") AND (Python OR Zapier) NOT senior
   Terms come from the role profile:
     - search_queries        → the job-title OR-group (always)
     - must_have  (optional) → each ANDed in
     - nice_to_have (optional) → an OR-group ANDed in
     - exclude_keywords      → NOT terms (reused from SEARCH_SETTINGS/role)

2. X-RAY FETCH  (the part a string-builder tool can't do)
   Google/DuckDuckGo "X-Ray" over the big ATS domains finds postings at
   companies that AREN'T in the hardcoded Greenhouse/Lever slug lists:
     site:boards.greenhouse.io ("IT Consultant" OR "Automation Consultant")
   Results are fetched via scraper_web's DuckDuckGo search and flow into
   jobs.csv tagged with role_hint, so they force-match the role and are
   deduped + relevance-filtered like everything else.

Plus SAVED-SEARCH ROWS: one clickable row per platform (LinkedIn, Google
X-Ray, Indeed) carrying the Boolean query, same pattern as the freelance
saved searches — for the boards you still want to browse by hand.

Activation: "boolean_search": True in a profile's SEARCH_SETTINGS (or the
--xray flag on run_scrape). Skip a run with --no-xray.

Standalone:
    python boolean_query.py --profile alex           # print strings per role
    python boolean_query.py --profile alex --fetch    # also run the X-Ray fetch
"""
import time

import requests

# X-Ray target ATS domains. Each returns individual job postings well via
# a `site:` search (Workday is intentionally omitted — its X-Ray results
# are mostly search landing pages, not postings).
XRAY_SITES = {
    "Greenhouse": "boards.greenhouse.io",
    "Lever": "jobs.lever.co",
    "Ashby": "jobs.ashbyhq.com",
}


def _phrase(term: str) -> str:
    """Quote multi-word terms so the platform treats them as a phrase."""
    term = (term or "").strip()
    return f'"{term}"' if " " in term else term


def role_terms(role: dict, default_exclude: list = None) -> dict:
    """Pull the four term groups out of a role profile."""
    return {
        "titles": [t for t in role.get("search_queries", []) if t],
        "must": [t for t in role.get("must_have", []) if t],
        "nice": [t for t in role.get("nice_to_have", []) if t],
        "exclude": [t for t in (role.get("exclude_keywords")
                                or default_exclude or []) if t],
    }


def build_boolean(terms: dict, google_style: bool = False,
                  include_exclude: bool = True) -> str:
    """
    Compose a Boolean string from term groups.
      google_style=True  → exclusions render as -"term" (Google/X-Ray)
      google_style=False → exclusions render as NOT "term" (LinkedIn/ATS)
    """
    parts = []
    titles = terms.get("titles", [])
    if titles:
        parts.append("(" + " OR ".join(_phrase(t) for t in titles) + ")")
    for m in terms.get("must", []):
        parts.append(_phrase(m))
    nice = terms.get("nice", [])
    if nice:
        parts.append("(" + " OR ".join(_phrase(n) for n in nice) + ")")

    query = " AND ".join(parts)

    if include_exclude and terms.get("exclude"):
        if google_style:
            query += " " + " ".join(f'-{_phrase(e)}' for e in terms["exclude"])
        else:
            query += " " + " ".join(f'NOT {_phrase(e)}' for e in terms["exclude"])
    return query.strip()


# Whole-web X-Ray returns little on long queries, so cap the title
# OR-group. Exclusions are dropped here on purpose — the matcher applies
# exclude_keywords downstream, and long -"phrase" chains hurt DDG recall.
XRAY_MAX_TITLES = 4


def xray_query(site: str, terms: dict, location: str = "") -> str:
    """
    A `site:` X-Ray query. Deliberately short — a capped title OR-group
    only. Location appended only when it's a real place (not "Remote",
    which just suppresses results).
    """
    core_terms = {"titles": terms.get("titles", [])[:XRAY_MAX_TITLES]}
    core = build_boolean(core_terms, google_style=True, include_exclude=False)
    q = f"site:{site} {core}"
    if location and location.strip().lower() not in ("remote", "anywhere", ""):
        q += f" {location.strip()}"
    return q.strip()


# ═══════════════════════════════════════════════════════════
# Saved-search rows — clickable Boolean/X-Ray links per platform
# ═══════════════════════════════════════════════════════════

def _q(text: str) -> str:
    return requests.utils.quote(text)


def search_strings(role: dict, location: str = "",
                   default_exclude: list = None) -> dict:
    """
    Plain-data view of a role's search strings for display (Admin Panel).
    No network, no JobListing — just the strings and clickable URLs.
    """
    terms = role_terms(role, default_exclude)
    boolean_ln = build_boolean(terms, google_style=False)
    loc = "" if location.strip().lower() in ("remote", "anywhere") else location

    li = f"https://www.linkedin.com/jobs/search/?keywords={_q(boolean_ln)}&f_TPR=r604800&sortBy=DD"
    ind = f"https://www.indeed.com/jobs?q={_q(boolean_ln)}&sort=date&fromage=7"
    if loc:
        li += f"&location={_q(loc)}"
        ind += f"&l={_q(loc)}"

    xray = []
    for name, site in XRAY_SITES.items():
        gq = xray_query(site, terms, location)
        xray.append({
            "site": name,
            "query": gq,
            "url": f"https://www.google.com/search?q={_q(gq)}",
        })

    return {
        "boolean": boolean_ln,
        "linkedin_url": li,
        "indeed_url": ind,
        "xray": xray,
    }


def saved_search_rows(role_id: str, role: dict, location: str = "",
                      default_exclude: list = None) -> list:
    """One clickable row per platform, carrying the Boolean query."""
    from scraper import JobListing

    terms = role_terms(role, default_exclude)
    boolean_ln = build_boolean(terms, google_style=False)
    boolean_short = boolean_ln[:70] + ("…" if len(boolean_ln) > 70 else "")
    loc = "" if location.strip().lower() in ("remote", "anywhere") else location

    rows = []

    # LinkedIn (Boolean keywords, last 7 days, newest first)
    li = f"https://www.linkedin.com/jobs/search/?keywords={_q(boolean_ln)}&f_TPR=r604800&sortBy=DD"
    if loc:
        li += f"&location={_q(loc)}"
    rows.append(("LinkedIn (Boolean)", li,
                 "Boolean keyword search, past week, newest first"))

    # Indeed (Boolean)
    ind = f"https://www.indeed.com/jobs?q={_q(boolean_ln)}&sort=date&fromage=7"
    if loc:
        ind += f"&l={_q(loc)}"
    rows.append(("Indeed (Boolean)", ind, "Boolean search, last 7 days"))

    # Google X-Ray, one row per ATS domain
    for name, site in XRAY_SITES.items():
        gq = xray_query(site, terms, location)
        url = f"https://www.google.com/search?q={_q(gq)}"
        rows.append((f"Google X-Ray → {name}", url,
                     f"Finds {name} postings at companies not in your slug lists"))

    out = []
    for name, url, note in rows:
        out.append(JobListing(
            title=f"🔎 {name}: {boolean_short}",
            company=f"{name} (manual search)",
            location="Remote" if not loc else loc,
            url=url,
            source=name.split(" ")[0],
            description=f"{note}. Boolean: {boolean_ln}",
            apply_method="✍️ Manual",
            role_hint=role_id,
        ))
    return out


# ═══════════════════════════════════════════════════════════
# X-Ray FETCH — run the site: queries and return real postings
# ═══════════════════════════════════════════════════════════

def run_xray_search(role_id: str, role: dict, location: str = "",
                    max_results: int = 15, default_exclude: list = None) -> list:
    """
    Execute the X-Ray queries against DuckDuckGo (or SerpAPI if configured)
    and return real job postings as JobListing rows tagged with role_hint.
    """
    from scraper import JobListing
    from scraper_web import _search_duckduckgo, _search_google_serpapi, \
        _is_job_url, _extract_company_from_url
    import os

    terms = role_terms(role, default_exclude)
    if not terms["titles"]:
        return []

    has_serpapi = bool(os.getenv("SERPAPI_KEY", ""))
    engine = _search_google_serpapi if has_serpapi else _search_duckduckgo

    jobs, seen = [], set()
    for name, site in XRAY_SITES.items():
        gq = xray_query(site, terms, location)
        results = []
        # Free DuckDuckGo intermittently 202-"challenge" throttles; one
        # retry after a cooldown recovers most of those. SerpAPI doesn't
        # need it but the retry is harmless there.
        for attempt in range(2):
            try:
                results = engine(gq, max_results=10)
            except Exception as e:
                print(f"    [X-Ray/{name}] Error: {e}")
                results = []
            if results:
                break
            time.sleep(2.0)
        for r in results:
            url = r.get("url", "")
            title = r.get("title", "")
            if not url or not title or not _is_job_url(url):
                continue
            if url in seen:
                continue
            seen.add(url)
            # Trim ATS boilerplate like "Job Application for X at Y"
            clean = title.replace("Job Application for", "").strip(" -–—")
            jobs.append(JobListing(
                title=clean or title,
                company=_extract_company_from_url(url),
                location=location or "Remote",
                url=url,
                source=f"X-Ray ({name})",
                description=r.get("snippet", "")[:500],
                apply_method="📋 Form Fill",
                role_hint=role_id,
            ))
            if len(jobs) >= max_results:
                break
        time.sleep(1.0)  # DuckDuckGo rate limit

    if jobs:
        print(f"  🛰️  X-Ray: {len(jobs)} postings for role '{role_id}'")
    else:
        note = "" if os.getenv("SERPAPI_KEY") else \
            " (free DuckDuckGo may be throttling — the clickable Google " \
            "X-Ray rows still work; set SERPAPI_KEY for a reliable fetch)"
        print(f"  🛰️  X-Ray: 0 postings for role '{role_id}'{note}")
    return jobs


# ═══════════════════════════════════════════════════════════
# Entry point — called from run_scrape.py (Step 1e)
# ═══════════════════════════════════════════════════════════

def scrape_boolean_sources(roles: dict, location: str = "",
                           do_fetch: bool = True, max_results: int = 15,
                           default_exclude: list = None) -> list:
    """
    For every role: emit the saved-search rows, and (when do_fetch) run the
    X-Ray fetch. Returns a combined JobListing list for the pipeline.
    """
    all_jobs, seen = [], set()

    def _add(rows):
        for j in rows:
            if j.job_id not in seen:
                seen.add(j.job_id)
                all_jobs.append(j)

    for role_id, role in roles.items():
        _add(saved_search_rows(role_id, role, location, default_exclude))
        if do_fetch:
            _add(run_xray_search(role_id, role, location, max_results, default_exclude))

    print(f"  🧭 Boolean/X-Ray sources: {len(all_jobs)} rows")
    return all_jobs


if __name__ == "__main__":
    import argparse
    from config import ROLE_PROFILES, SEARCH_SETTINGS

    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="Profile to use")
    parser.add_argument("--fetch", action="store_true",
                        help="Also run the live X-Ray fetch (network)")
    args = parser.parse_args()

    default_exclude = SEARCH_SETTINGS.get("exclude_keywords", [])
    locations = SEARCH_SETTINGS.get("locations", ["Remote"])
    location = locations[0] if locations else "Remote"

    for rid, role in ROLE_PROFILES.items():
        terms = role_terms(role, default_exclude)
        print(f"\n{'='*66}\n  {role.get('label', rid)}  [{rid}]\n{'='*66}")
        print("  LinkedIn/ATS Boolean:")
        print(f"    {build_boolean(terms)}")
        for name, site in XRAY_SITES.items():
            print(f"  Google X-Ray → {name}:")
            print(f"    {xray_query(site, terms, location)}")

    if args.fetch:
        print(f"\n{'='*66}\n  LIVE X-RAY FETCH\n{'='*66}")
        jobs = scrape_boolean_sources(ROLE_PROFILES, location, do_fetch=True,
                                      default_exclude=default_exclude)
        for j in jobs:
            if j.source.startswith("X-Ray"):
                print(f"    [{j.source}] {j.title[:55]:55}  {j.company}")
