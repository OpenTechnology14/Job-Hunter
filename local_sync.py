"""
Local Spreadsheet Sync
Same interface as sheets_sync.py but writes to a local CSV file.
Open it in Excel, LibreOffice, Numbers, or any spreadsheet app.

The CSV lives at: output/{profile}/jobs.csv

Usage:
    from local_sync import push_jobs, pull_ready_jobs, mark_applied
"""
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path

import re
from email.utils import parsedate_to_datetime

from config import SHEET_COLUMNS, DATA_DIR, PROFILE_DIR, LOCATION_FILTER, SEARCH_SETTINGS


def _build_location_set() -> set:
    """Build the set of nearby city names (lowercase) from profile config."""
    cities = {LOCATION_FILTER["city"].lower()}
    for c in LOCATION_FILTER.get("nearby_cities", []):
        cities.add(c.lower())
    return cities


NEARBY_CITIES = _build_location_set()
_state = LOCATION_FILTER.get("state", "").lower()
_state_full = {
    "nh": "new hampshire", "ma": "massachusetts", "ct": "connecticut",
    "me": "maine", "vt": "vermont", "ri": "rhode island", "ny": "new york",
    "ca": "california", "tx": "texas", "fl": "florida", "wa": "washington",
    "co": "colorado", "il": "illinois", "ga": "georgia", "pa": "pennsylvania",
    "oh": "ohio", "nc": "north carolina", "va": "virginia", "mi": "michigan",
}.get(_state, "")


def _detect_work_type(job: dict) -> str:
    """Infer Remote/Hybrid/On-site from location and description fields."""
    location = (job.get("location", "") or "").lower()
    title = (job.get("title", "") or "").lower()
    desc = (job.get("description", "") or "").lower()
    source = (job.get("source", "") or "").lower()

    if source == "remoteok":
        return "Remote"

    combined = f"{location} {title} {desc}"

    if re.search(r'\bhybrid\b', combined):
        return "Hybrid"
    if re.search(r'\bremote\b', combined):
        return "Remote"
    if re.search(r'\bon[- ]?site\b|\bin[- ]?office\b|\bin[- ]?person\b', combined):
        return "On-site"

    if location:
        return "On-site"

    return "Unknown"


GENERIC_LOCATIONS = {
    "united states", "usa", "us", "worldwide", "global", "anywhere",
    "north america", "multiple locations", "various locations",
    "united states of america",
}


# ── Foreign location detection ──────────────────────────
# If a "Remote" job's location contains any of these and does NOT contain
# a US indicator, it's an international posting — reject it.
_FOREIGN_COUNTRIES = {
    "philippines", "germany", "australia", "canada", "united kingdom",
    "india", "mexico", "colombia", "argentina", "brazil", "chile",
    "france", "austria", "netherlands", "ireland", "singapore", "japan",
    "south africa", "new zealand", "albania", "poland", "romania",
    "spain", "italy", "sweden", "norway", "denmark", "finland",
    "switzerland", "portugal", "czech", "hungary", "croatia", "serbia",
    "turkey", "egypt", "nigeria", "kenya", "ghana", "pakistan",
    "bangladesh", "vietnam", "thailand", "indonesia", "malaysia",
    "taiwan", "south korea", "israel", "qatar", "kuwait", "bahrain",
    "jordan", "lebanon", "morocco", "tunisia", "saudi arabia",
    "united arab emirates", "uae", "cuba", "ecuador", "haiti",
    "honduras", "nicaragua", "panama", "bolivia", "peru", "uruguay",
    "paraguay", "venezuela", "costa rica", "dominican republic",
    "jamaica", "trinidad", "china", "hong kong", "myanmar", "cambodia",
    "sri lanka", "nepal", "ukraine", "belarus", "russia", "georgia",
    "armenia", "azerbaijan", "uzbekistan", "kazakhstan",
    "zimbabwe", "zambia", "tanzania", "uganda", "rwanda", "ethiopia",
    "cameroon", "senegal", "botswana", "namibia", "malawi", "burundi",
    "iran", "iraq", "oman", "algeria", "libya",
    "syria", "yemen", "afghanistan",
    "guatemala", "el salvador", "belize",
}
_FOREIGN_REGIONS = {
    "emea", "latam", "apac", "asia pacific", "europe", "asia",
    "africa", "middle east", "latin america", "caribbean",
    "eu ", "uk ",
}
# Common foreign cities that show up in remote listings
_FOREIGN_CITIES = {
    "london", "berlin", "munich", "frankfurt", "hamburg", "paris",
    "dublin", "amsterdam", "toronto", "vancouver", "sydney",
    "melbourne", "mumbai", "bangalore", "hyderabad", "delhi",
    "tokyo", "shanghai", "beijing", "seoul", "taipei",
    "kiel", "gummersbach", "ingolstadt", "bamberg", "jakobsdorf",
    "mannheim", "düsseldorf", "stuttgart", "cologne", "vienna",
    "zurich", "geneva", "brussels", "barcelona", "madrid", "lisbon",
    "rome", "milan", "warsaw", "prague", "budapest", "bucharest",
    "copenhagen", "stockholm", "oslo", "helsinki",
    "são paulo", "rio de janeiro", "buenos aires", "bogotá",
    "mexico city", "guadalajara", "monterrey", "santiago",
    "cape town", "johannesburg", "nairobi", "lagos", "accra",
    "cairo", "tel aviv", "dubai", "riyadh", "doha",
    "kuala lumpur", "jakarta", "bangkok", "ho chi minh",
    "manila", "cebu",
    "kreuztal", "traunstein", "salzburg",
}

_US_INDICATORS = {
    "united states", "usa", " us", "u.s.", "united states of america",
}
# All 50 US state names (lowercase) for location matching
_US_STATES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
    "maine", "maryland", "massachusetts", "michigan", "minnesota",
    "mississippi", "missouri", "montana", "nebraska", "nevada",
    "new hampshire", "new jersey", "new mexico", "new york",
    "north carolina", "north dakota", "ohio", "oklahoma", "oregon",
    "pennsylvania", "rhode island", "south carolina", "south dakota",
    "tennessee", "texas", "utah", "vermont", "virginia", "washington",
    "west virginia", "wisconsin", "wyoming", "district of columbia",
}
_US_STATE_ABBRS = {
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga",
    "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md",
    "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj",
    "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc",
    "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy", "dc",
}


def _is_us_compatible_remote(location: str) -> bool:
    """
    Check if a Remote job's location is compatible with a US-based applicant.

    Logic (default-deny for foreign locations):
      1. Empty or just "Remote" → accept (no country restriction stated)
      2. Check for foreign indicators — if found AND US is also present, it's
         multi-country (reject). If found without US, also reject.
      3. Contains a US indicator ("United States", "USA", etc.) → accept
      4. Contains a US state name or nearby city → accept
      5. Generic location we can't classify → accept (benefit of doubt)
    """
    loc = location.lower().strip()

    # 1. Empty or just "Remote" — no country restriction
    if not loc or loc == "remote":
        return True

    # Strip "remote" prefix for analysis: "Remote — Berlin" → "berlin"
    cleaned = re.sub(r'^remote[\s—–\-,;:]*', '', loc).strip()

    # 2. Check for foreign indicators FIRST (before US check)
    #    This catches "Australia, Canada, United States" as multi-country
    has_foreign = False
    for country in _FOREIGN_COUNTRIES:
        if country in loc:
            has_foreign = True
            break
    if not has_foreign:
        for region in _FOREIGN_REGIONS:
            if region in loc:
                has_foreign = True
                break
    if not has_foreign:
        for city in _FOREIGN_CITIES:
            if city in cleaned:
                has_foreign = True
                break

    if has_foreign:
        return False  # Foreign indicator found — reject regardless of US mention

    # 3. Contains a US indicator
    for ind in _US_INDICATORS:
        if ind in loc:
            return True

    # 4. Check for US state names (full or abbreviated)
    for state in _US_STATES:
        if state in loc:
            return True
    # Check abbreviations only as whole words: "Remote, NH" but not "Nashua"
    for abbr in _US_STATE_ABBRS:
        if re.search(r'\b' + re.escape(abbr) + r'\b', loc):
            return True

    # Check against profile's nearby cities
    for city in NEARBY_CITIES:
        if city in loc:
            return True

    # 5. Location we can't classify — accept (benefit of doubt)
    return True


def _is_nearby_or_remote(job: dict, work_type: str) -> bool:
    """Return True only for Remote jobs or jobs near the configured location."""
    # Always reject Unknown work type
    if work_type == "Unknown":
        return False

    if work_type == "Remote" and LOCATION_FILTER.get("include_remote", True):
        location = (job.get("location", "") or "")
        return _is_us_compatible_remote(location)

    location = (job.get("location", "") or "").lower().strip()

    # Reject generic country-level locations that aren't marked remote
    if location in GENERIC_LOCATIONS:
        return False

    for city in NEARBY_CITIES:
        if city in location:
            return True

    if _state and re.search(r'\b' + re.escape(_state) + r'\b', location):
        return True
    if _state_full and _state_full in location:
        return True

    return False


def _normalize_date(raw) -> str:
    """
    Normalize a date from any scraper format to YYYY-MM-DD.

    Handles:
      - Unix timestamps (int or numeric string)
      - ISO 8601 strings ("2026-05-15T08:44:57-04:00")
      - Simple date strings ("2026-05-15")
      - Empty / None → ""
    """
    if not raw:
        return ""

    # Unix timestamp (int)
    if isinstance(raw, (int, float)):
        try:
            return datetime.fromtimestamp(raw).strftime("%Y-%m-%d")
        except (OSError, ValueError):
            return ""

    raw = str(raw).strip()
    if not raw:
        return ""

    # Numeric string → Unix timestamp
    if raw.isdigit():
        try:
            return datetime.fromtimestamp(int(raw)).strftime("%Y-%m-%d")
        except (OSError, ValueError):
            return ""

    # Already YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        return raw

    # ISO 8601 with timezone ("2026-05-15T08:44:57-04:00" or "...+00:00" or "...Z")
    try:
        # Python 3.11+ handles most ISO formats
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        pass

    # Fallback: grab YYYY-MM-DD from the beginning of any string
    m = re.match(r"(\d{4}-\d{2}-\d{2})", raw)
    if m:
        return m.group(1)

    return ""


JOBS_FILE = PROFILE_DIR / "jobs.csv"


def _ensure_file():
    """Create the CSV with headers if it doesn't exist."""
    if not JOBS_FILE.exists():
        with open(JOBS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(SHEET_COLUMNS)
        print(f"  📄 Created: {JOBS_FILE}")


def _read_all_rows() -> list[dict]:
    """Read all rows from the CSV as dicts."""
    _ensure_file()
    with open(JOBS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _write_all_rows(rows: list[dict]):
    """Overwrite the CSV with the given rows."""
    with open(JOBS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SHEET_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _get_existing_urls() -> set:
    rows = _read_all_rows()
    return {row.get("URL", "") for row in rows}


def cleanup_stale_jobs(**kwargs):
    """
    Remove old unapproved jobs from the CSV based on job posting date.

    Controlled by SEARCH_SETTINGS:
      stale_days: int  — remove unapproved jobs older than this (default: 21, 0 = disabled)

    Uses the job's posting date ("Date Posted") as the primary staleness check.
    Falls back to "Date Found" if no posting date is available.

    Rules:
      - Jobs with Apply = "Y", "Done", or any non-empty approval are NEVER removed
      - Jobs with Apply = "N" are removed after stale_days
      - Jobs with Apply = "" (blank/unreviewed) are removed after stale_days
      - Jobs with no date at all are left alone (legacy data)

    Returns the number of jobs removed.
    """
    stale_days = SEARCH_SETTINGS.get("stale_days", 21)
    if stale_days <= 0:
        return 0

    _ensure_file()
    rows = _read_all_rows()
    if not rows:
        return 0

    cutoff = datetime.now() - timedelta(days=stale_days)
    keep = []
    removed = 0

    for row in rows:
        apply_val = (row.get("Apply", "") or "").strip().upper()

        # Never remove approved or applied jobs
        if apply_val in ("Y", "DONE") or apply_val.startswith("DONE"):
            keep.append(row)
            continue

        # Use Date Posted first, fall back to Date Found
        date_str = (row.get("Date Posted", "") or "").strip()
        date_source = "posted"
        if not date_str:
            date_str = (row.get("Date Found", "") or "").strip()
            date_source = "found"

        if not date_str:
            keep.append(row)  # No date at all — keep (legacy data)
            continue

        try:
            job_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            keep.append(row)  # Unparseable date — keep
            continue

        if job_date < cutoff:
            removed += 1  # Stale + unapproved — remove
        else:
            keep.append(row)

    if removed > 0:
        _write_all_rows(keep)
        print(f"  🧹 Cleaned up {removed} stale jobs (posted more than {stale_days} days ago, unapproved)")

    return removed


def push_jobs(jobs: list[dict], **kwargs):
    """Append matched jobs to the local CSV. Skips duplicates by URL."""
    _ensure_file()
    existing_urls = _get_existing_urls()
    today = datetime.now().strftime("%Y-%m-%d")

    new_rows = []
    skipped = 0
    for job in jobs:
        url = job.get("url", "")
        if url in existing_urls:
            continue

        work_type = _detect_work_type(job)

        if not _is_nearby_or_remote(job, work_type):
            skipped += 1
            continue

        new_rows.append({
            "Job Title": job.get("title", ""),
            "Company": job.get("company", ""),
            "Location": job.get("location", ""),
            "Work Type": work_type,
            "Salary": job.get("salary", ""),
            "Role Category": job.get("role_category_label", "Unmatched"),
            "Match Reason": job.get("match_reason", ""),
            "Apply Method": job.get("apply_method", "✍️ Manual"),
            "Apply": "",
            "Resume Version": job.get("recommended_resume", ""),
            "URL": url,
            "Source": job.get("source", ""),
            "Date Posted": _normalize_date(job.get("date_posted", "")),
            "Date Found": today,
            "Date Applied": "",
            "Notes": "",
        })

    if skipped:
        print(f"  ⏭️  Skipped {skipped} jobs (not Remote or near Nashua NH)")

    if not new_rows:
        print("  No new jobs to add.")
        return

    # Append to CSV
    with open(JOBS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SHEET_COLUMNS)
        for row in new_rows:
            writer.writerow(row)

    print(f"  ✅ Added {len(new_rows)} jobs to {JOBS_FILE.name}")

    methods = {}
    for row in new_rows:
        m = row["Apply Method"]
        methods[m] = methods.get(m, 0) + 1
    for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
        print(f"    {method}: {count}")


def pull_ready_jobs(**kwargs) -> list[dict]:
    """Pull jobs where Apply column is Y (case-insensitive)."""
    rows = _read_all_rows()
    ready = []

    for i, row in enumerate(rows):
        apply_val = (row.get("Apply", "") or "").strip().upper()
        if apply_val == "Y":
            ready.append({
                "csv_row_index": i,
                "title": row.get("Job Title", ""),
                "company": row.get("Company", ""),
                "location": row.get("Location", ""),
                "salary": row.get("Salary", ""),
                "role_category_label": row.get("Role Category", ""),
                "apply_method": row.get("Apply Method", ""),
                "recommended_resume": row.get("Resume Version", ""),
                "url": row.get("URL", ""),
                "source": row.get("Source", ""),
            })

    print(f"  📋 {len(ready)} jobs marked 'Y' to apply in {JOBS_FILE.name}")
    return ready


def mark_applied(ws_unused, row_index, resume_used: str = ""):
    """
    Mark a job as applied in the local CSV.
    row_index is csv_row_index from pull_ready_jobs.
    ws_unused is accepted for interface compatibility but ignored.
    """
    rows = _read_all_rows()
    today = datetime.now().strftime("%Y-%m-%d")

    idx = row_index if isinstance(row_index, int) else -1

    if 0 <= idx < len(rows):
        rows[idx]["Apply"] = "Done"
        rows[idx]["Date Applied"] = today
        if resume_used:
            rows[idx]["Resume Version"] = resume_used
        _write_all_rows(rows)


def sync_scraped_to_sheet(input_file: str = None):
    """Load matched jobs from JSON and push to local CSV."""
    if input_file:
        job_file = Path(input_file)
    else:
        files = sorted(DATA_DIR.glob("matched_jobs_*.json"), reverse=True)
        if not files:
            files = sorted(DATA_DIR.glob("raw_jobs_*.json"), reverse=True)
        if not files:
            print("No job files found. Run scraper first.")
            return
        job_file = files[0]

    print(f"  Loading: {job_file}")
    with open(job_file) as f:
        jobs = json.load(f)

    push_jobs(jobs)
    print(f"\n  📄 Open in your spreadsheet app: {JOBS_FILE}")


# ── get_worksheet stub for interface compatibility ────────

def get_worksheet(**kwargs):
    """Stub — local mode doesn't need a worksheet object."""
    return None


if __name__ == "__main__":
    sync_scraped_to_sheet()
