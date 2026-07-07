"""
Quality Filter — post-match result hygiene, built into the pipeline.

Codifies the manual review rules that used to happen by eyeball:

  1. TITLE RELEVANCE   — a matched job's title must contain a keyword from
                         its role's search queries. Catches freelance projects
                         that only matched on a stray description word
                         (the "sourdough chef" problem).
  2. CURRENCY / BUDGET — non-USD budgets are foreign-client gigs (₹600
                         projects); micro-budgets below a floor aren't worth
                         a proposal. Budget floor applies to freelance
                         project sources only.
  3. AGGREGATOR PAGES  — web-search results that are search-listing pages,
                         not job posts ("1,000+ It Consultant jobs - LinkedIn").
  4. DUPLICATES        — normalized title+company dedupe within a batch
                         (cross-source dupes have different URLs, so the
                         URL dedupe in local_sync can't catch them).

All filters are config-driven via SEARCH_SETTINGS (profile-overridable,
toggleable in the Admin Panel → Config → Result Quality Filters):

    "filter_title_relevance": True,
    "filter_usd_only": True,
    "filter_min_budget": 25,     # USD, 0 = disabled
    "filter_aggregators": True,

Saved-search rows (🔎 Upwork/Guru/... links) are always exempt — they're
navigation aids, not postings.

Retro-clean an existing CSV (only unreviewed/rejected rows are touched):

    python quality_filter.py --profile alex --clean --dry-run
    python quality_filter.py --profile alex --clean
"""
import re

from config import ROLE_PROFILES, SEARCH_SETTINGS


# Sources whose rows are freelance PROJECTS (budget floor applies).
FREELANCE_PROJECT_SOURCES = {"Freelancer.com"}

# Sources whose rows come from open web search (aggregator filter applies).
WEB_SEARCH_SOURCES = {"Web Search"}

_NON_USD_RE = re.compile(r"[₹€£¥₩₽₪₺₴]|R\$|A\$|C\$|CHF|SEK|NOK|DKK|PLN|zł")

_AGGREGATOR_TITLE_RE = re.compile(
    r"\b\d[\d,]*\+?\s+(?:[a-z ]{0,20})?jobs?\b"      # "1,000+ It Consultant jobs"
    r"|\bjobs?\s+(?:hiring|available)\b"              # "Jobs Hiring Now"
    r"|\bhiring now\b"
    r"|\bapply now\b.*\|"                             # "... Apply Now | site.com"
    r"|\bjobs? in [a-z ]+\b.*(?:linkedin|indeed|ziprecruiter|glassdoor)",
    re.IGNORECASE,
)
_AGGREGATOR_URL_RE = re.compile(
    r"linkedin\.com/jobs/search"
    r"|indeed\.com/(?:q-|jobs\?)"
    r"|ziprecruiter\.com/(?:jobs-search|candidate/search|[a-z-]*jobs)"
    r"|glassdoor\.com/job(?:s|-listing)?/"
    r"|remoterocketship\.com"
    r"|/search\?",
    re.IGNORECASE,
)


def _norm_key(title: str, company: str) -> str:
    """Normalized title+company key for cross-source duplicate detection."""
    def norm(s):
        s = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())
        return re.sub(r"\s+", " ", s).strip()
    return f"{norm(title)}|{norm(company)}"


def _is_saved_search_row(job: dict) -> bool:
    """Saved-search navigation rows (🔎 Upwork search: ...) are always kept."""
    return "(manual search)" in (job.get("company", "") or "") \
        or (job.get("title", "") or "").startswith("🔎")


def _role_tokens(role: dict) -> set:
    """Significant words from a role's queries + optional relevance_keywords."""
    tokens = set()
    for q in role.get("search_queries", []):
        for w in q.lower().split():
            if len(w) >= 3:
                tokens.add(w)
    for w in role.get("relevance_keywords", []):
        tokens.add(w.lower())
    # Light stemming: "automation" should also match "automate(d)",
    # "consulting" should match "consultant"/"consultancy". Tokens are
    # matched as word prefixes, so adding the stem is enough.
    for t in list(tokens):
        for suffix in ("ation", "ing", "ant", "er"):
            if t.endswith(suffix) and len(t) - len(suffix) >= 4:
                tokens.add(t[: -len(suffix)])
    return tokens


def _title_is_relevant(title: str, role: dict) -> bool:
    tokens = _role_tokens(role)
    if not tokens:
        return True
    title_lower = (title or "").lower()
    return any(re.search(r"\b" + re.escape(t), title_lower) for t in tokens)


def evaluate_job(job: dict, settings: dict = None) -> str:
    """
    Run one job dict through the quality rules (dedupe excluded — that
    needs batch state). Returns "" if the job passes, otherwise the
    drop reason. Shared by the pipeline filter and the CSV retro-clean.
    """
    s = settings or SEARCH_SETTINGS

    if _is_saved_search_row(job):
        return ""

    title = job.get("title", "") or ""
    salary = job.get("salary", "") or ""
    source = job.get("source", "") or ""
    url = job.get("url", "") or ""

    # 3. Aggregator search-listing pages (web search results only)
    if s.get("filter_aggregators", True) and source in WEB_SEARCH_SOURCES:
        if _AGGREGATOR_TITLE_RE.search(title) or _AGGREGATOR_URL_RE.search(url):
            return "aggregator page"

    # 2a. Non-USD budget/salary → foreign-client gig
    if s.get("filter_usd_only", True) and salary and _NON_USD_RE.search(salary):
        return "non-USD pay"

    # 2b. Micro-budget freelance projects
    min_budget = int(s.get("filter_min_budget", 25) or 0)
    if min_budget and source in FREELANCE_PROJECT_SOURCES:
        amounts = [int(a.replace(",", ""))
                   for a in re.findall(r"\$([\d,]+)", salary)]
        if amounts and max(amounts) < min_budget:
            return f"budget under ${min_budget}"

    # 1. Title relevance against the matched role's keywords
    if s.get("filter_title_relevance", True):
        role = ROLE_PROFILES.get(job.get("role_category", ""))
        if role and not _title_is_relevant(title, role):
            return "title unrelated to role keywords"

    return ""


def apply_quality_filters(jobs: list[dict], settings: dict = None) -> list[dict]:
    """
    Filter a list of matched job dicts. Prints a per-reason summary so
    nothing is dropped silently. Returns the kept jobs.
    """
    kept = []
    dropped = {}   # reason -> [titles]
    seen_keys = set()

    for job in jobs:
        reason = evaluate_job(job, settings)
        if not reason:
            key = _norm_key(job.get("title", ""), job.get("company", ""))
            if key in seen_keys:
                reason = "duplicate (title+company)"
            else:
                seen_keys.add(key)

        if reason:
            dropped.setdefault(reason, []).append(job.get("title", "")[:60])
        else:
            kept.append(job)

    total_dropped = sum(len(v) for v in dropped.values())
    if total_dropped:
        print(f"\n  🧽 Quality filter: dropped {total_dropped} of {len(jobs)} jobs")
        for reason, titles in sorted(dropped.items(), key=lambda x: -len(x[1])):
            sample = "; ".join(titles[:3])
            print(f"     · {len(titles)} {reason}  (e.g. {sample})")

    return kept


# ═══════════════════════════════════════════════════════════
# Retro-clean: apply the same rules to an existing jobs.csv
# ═══════════════════════════════════════════════════════════

def _csv_row_to_job(row: dict) -> dict:
    """Map a jobs.csv row into the dict shape the filters expect."""
    label = row.get("Role Category", "") or ""
    role_id = ""
    for rid, role in ROLE_PROFILES.items():
        if role.get("label", "") == label:
            role_id = rid
            break
    return {
        "title": row.get("Job Title", ""),
        "company": row.get("Company", ""),
        "salary": row.get("Salary", ""),
        "source": row.get("Source", ""),
        "url": row.get("URL", ""),
        "role_category": role_id,
    }


def clean_csv(dry_run: bool = False) -> int:
    """
    Re-apply the quality filters to the existing jobs.csv.
    Approved/applied rows (Apply = Y/Done) are never touched and still
    claim their title+company key, so a junk duplicate of an approved
    job gets removed rather than the other way around.
    Returns the number of rows removed.
    """
    from local_sync import _read_all_rows, _write_all_rows, JOBS_FILE

    rows = _read_all_rows()
    if not rows:
        print("  jobs.csv is empty — nothing to clean.")
        return 0

    keep, removable = [], []
    seen_keys = set()

    for row in rows:
        apply_val = (row.get("Apply", "") or "").strip().upper()
        protected = apply_val == "Y" or apply_val.startswith("DONE")

        job = _csv_row_to_job(row)
        key = _norm_key(job["title"], job["company"])

        if protected:
            seen_keys.add(key)
            keep.append(row)
            continue

        reason = evaluate_job(job)
        if not reason and key in seen_keys:
            reason = "duplicate (title+company)"

        if reason:
            removable.append((reason, row))
        else:
            seen_keys.add(key)
            keep.append(row)

    if not removable:
        print("  ✨ jobs.csv already clean — nothing to remove.")
        return 0

    print(f"\n  🧽 {'Would remove' if dry_run else 'Removing'} {len(removable)} rows from {JOBS_FILE.name}:")
    by_reason = {}
    for reason, row in removable:
        by_reason.setdefault(reason, []).append(row.get("Job Title", "")[:60])
    for reason, titles in sorted(by_reason.items(), key=lambda x: -len(x[1])):
        print(f"     · {len(titles)} {reason}")
        for t in titles[:5]:
            print(f"         - {t}")

    if not dry_run:
        _write_all_rows(keep)
        print(f"  ✅ jobs.csv now has {len(keep)} rows")

    return len(removable)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="Profile to use")
    parser.add_argument("--clean", action="store_true",
                        help="Re-apply quality filters to the existing jobs.csv")
    parser.add_argument("--dry-run", action="store_true",
                        help="With --clean: show what would be removed, change nothing")
    args = parser.parse_args()

    if args.clean:
        clean_csv(dry_run=args.dry_run)
    else:
        print("Nothing to do. Use --clean [--dry-run] to scrub the existing jobs.csv.")
