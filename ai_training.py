"""
AI Training / Data Annotation Job Module

Two things live here:

1. A curated PLATFORM DIRECTORY of AI-training gig platforms
   (DataAnnotation, Outlier, Alignerr, Mercor, ...). These are signup-based
   marketplaces, not job postings — you create an account, pass an
   assessment, then pick up paid tasks. The directory is shown in the
   Admin Panel (AI Training page) with per-platform signup status tracking.

2. SCRAPERS for real job postings at AI-training companies:
   - Ashby public job-board API (no auth) — Mercor, Micro1, etc.
   - Greenhouse boards for AI-labs/data companies (xAI, Scale AI, ...)
   - Lever boards (Welocalize, ...)
   Postings are filtered to training/annotation-type roles and flow into
   the normal jobs.csv pipeline with role_hint="ai-training".

IMPORTANT — HUMAN-ONLY WORK POLICY:
Every platform in this directory prohibits submitting AI-generated work
and actively screens for it (watermark checks, style analysis, honeypot
tasks). Accounts get banned and pay clawed back. This module automates
FINDING and TRACKING these gigs; the task work itself must be your own.

Usage:
    python ai_training.py --profile alex      # print directory + test scrape
    from ai_training import scrape_ai_training_sources, AI_TRAINING_PLATFORMS
"""
import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests

# NOTE: `from scraper import JobListing` happens lazily inside the scrape
# functions. Importing scraper pulls in config, which loads the active
# profile — a side effect the Admin Panel server must avoid when it only
# needs the platform directory and tracker helpers below.
_PROJECT_ROOT = Path(__file__).parent

HEADERS = {
    "User-Agent": "JobHunterBot/1.0 (personal job search automation)",
    "Accept": "application/json",
}


# ═══════════════════════════════════════════════════════════
# Platform directory — signup-based AI training marketplaces
# Pay figures are approximate public ranges (verify at signup).
# ═══════════════════════════════════════════════════════════

AI_TRAINING_PLATFORMS = [
    {
        "id": "dataannotation",
        "name": "DataAnnotation",
        "url": "https://www.dataannotation.tech",
        "focus": "Chatbot rating, coding tasks, writing/creative evaluation",
        "pay": "$20–$40+/hr (coding projects pay more)",
        "signup": "Direct signup → starter assessment (writing + logic)",
        "tier": "top pick",
        "notes": "Best general-purpose platform. Project volume varies week to "
                 "week. Coding assessment unlocks higher-paying queues. US-based, "
                 "pays via PayPal.",
    },
    {
        "id": "outlier",
        "name": "Outlier (Scale AI)",
        "url": "https://outlier.ai",
        "focus": "LLM response ranking, domain-expert Q&A, coding RLHF",
        "pay": "$15–$50/hr by domain expertise",
        "signup": "Resume upload → domain onboarding + assessments",
        "tier": "top pick",
        "notes": "Large task volume. Onboarding/assessment time is sometimes "
                 "unpaid or lower-paid. Domain experts (coding, STEM) earn the "
                 "higher rates.",
    },
    {
        "id": "alignerr",
        "name": "Alignerr (Labelbox)",
        "url": "https://www.alignerr.com",
        "focus": "Expert AI training — coding, STEM, law, medicine, languages",
        "pay": "$15–$150/hr depending on domain",
        "signup": "Application → AI-conducted video interview → matching",
        "tier": "top pick",
        "notes": "Higher quality bar, higher rates. IT/coding background maps "
                 "well to their technical annotation queues.",
    },
    {
        "id": "mercor",
        "name": "Mercor",
        "url": "https://work.mercor.com",
        "focus": "Contract work for AI labs — data work, evaluations, expert tasks",
        "pay": "$20–$100+/hr by role",
        "signup": "Resume upload → AI interview → auto-matching to open roles",
        "tier": "top pick",
        "notes": "One profile, many AI-lab contracts. Also posts real openings "
                 "(scraped automatically into jobs.csv via their Ashby board).",
    },
    {
        "id": "handshake-ai",
        "name": "Handshake AI",
        "url": "https://joinhandshake.com/ai",
        "focus": "AI tutoring / expert data for frontier labs",
        "pay": "$30–$100/hr (expert-level)",
        "signup": "Application with credentials → vetting",
        "tier": "expert",
        "notes": "Aimed at degree-holders and specialists. BS in CS qualifies "
                 "for technical tracks.",
    },
    {
        "id": "surge",
        "name": "Surge AI",
        "url": "https://www.surgehq.ai",
        "focus": "High-quality RLHF, red-teaming, evaluation for top labs",
        "pay": "$20–$45/hr typical",
        "signup": "Apply to be a 'Surger' → writing/quality assessment",
        "tier": "expert",
        "notes": "Selective. Strong writing sample matters more than credentials.",
    },
    {
        "id": "pareto",
        "name": "Pareto.AI",
        "url": "https://pareto.ai",
        "focus": "Expert data labeling and AI training projects",
        "pay": "$20–$150/hr by project",
        "signup": "Application → skills screening",
        "tier": "expert",
        "notes": "Project-based; queues open and close. Worth having an approved "
                 "profile waiting.",
    },
    {
        "id": "micro1",
        "name": "Micro1",
        "url": "https://www.micro1.ai",
        "focus": "AI trainer + technical contract marketplace",
        "pay": "$20–$60/hr",
        "signup": "AI interview → matched to remote AI/data roles",
        "tier": "general",
        "notes": "Single AI interview unlocks matching to multiple client roles.",
    },
    {
        "id": "prolific",
        "name": "Prolific",
        "url": "https://www.prolific.com",
        "focus": "Paid research studies incl. AI evaluation tasks",
        "pay": "~$8–$15/hr average",
        "signup": "Direct signup → demographic screening (waitlist possible)",
        "tier": "steady",
        "notes": "Lower pay but zero-stress filler between bigger platform tasks. "
                 "Legitimate academic + AI-lab studies.",
    },
    {
        "id": "crowdgen",
        "name": "CrowdGen (Appen)",
        "url": "https://www.crowdgen.com",
        "focus": "Search evaluation, data collection, transcription",
        "pay": "~$10–$25/hr",
        "signup": "Direct signup → per-project qualification exams",
        "tier": "steady",
        "notes": "Long-running rater projects (search/ads quality). Slower "
                 "onboarding, but steady hours once on a project.",
    },
    {
        "id": "telus-ai",
        "name": "TELUS Digital AI Community",
        "url": "https://www.telusdigital.com/careers/ai-community",
        "focus": "Search/ads rater, data collection, maps evaluation",
        "pay": "~$14/hr (US rater roles)",
        "signup": "Application → qualification exam per program",
        "tier": "steady",
        "notes": "Part-time capped hours (usually ~20/wk). Reliable long-term "
                 "side income.",
    },
    {
        "id": "welocalize",
        "name": "Welocalize",
        "url": "https://jobs.lever.co/welocalize",
        "focus": "Ads/search quality rating, linguistic AI data",
        "pay": "~$14–$18/hr",
        "signup": "Standard job application (also scraped via Lever board)",
        "tier": "steady",
        "notes": "W-2/contractor rater positions rather than gig tasks.",
    },
    {
        "id": "snorkel",
        "name": "Snorkel AI Expert Network",
        "url": "https://snorkel.ai/expert-data-contributors/",
        "focus": "Expert dataset contributions (coding, finance, medicine)",
        "pay": "$25–$100/hr by domain",
        "signup": "Expert network application",
        "tier": "expert",
        "notes": "Project-based expert work; technical background is a fit.",
    },
    {
        "id": "toloka",
        "name": "Toloka",
        "url": "https://toloka.ai",
        "focus": "Microtasks + expert AI tasks",
        "pay": "Variable, often low ($5–$20/hr)",
        "signup": "Direct signup",
        "tier": "backup",
        "notes": "Global microtask platform; expert track pays better than the "
                 "general queue. Lowest priority of the list.",
    },
    {
        "id": "turing",
        "name": "Turing",
        "url": "https://www.turing.com",
        "focus": "LLM training work for software developers",
        "pay": "$20–$50/hr (dev-focused)",
        "signup": "Developer profile + coding tests",
        "tier": "general",
        "notes": "Developer vetting is lengthy; LLM-trainer track is faster than "
                 "their full-time placement track.",
    },
]


# ═══════════════════════════════════════════════════════════
# Job-board scrapers — AI-training companies with public APIs
# ═══════════════════════════════════════════════════════════

# Ashby public job-board API (no auth):
#   https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true
ASHBY_AI_COMPANIES = [
    "mercor",
    "micro1",
    "openai",       # occasional human-data / evaluation roles
]

# Greenhouse boards of AI labs / data companies that post trainer,
# annotation, human-data, and rater roles. Unknown slugs 404 and are skipped.
GREENHOUSE_AI_COMPANIES = [
    "xai",                     # AI Tutor roles ($35–$65/hr)
    "scaleai",                 # Scale AI
    "invisibletechnologies",   # Invisible Tech — AI trainer contracts
    "snorkelai",
    "labelbox",
    "surgeai",
]

LEVER_AI_COMPANIES = [
    "welocalize",
]

# A posting on those boards is kept only if the title looks like
# training/annotation/human-data work (they also post regular SWE roles).
# Word boundaries matter: without \b, "rating" matches "Operating" and
# "trainer" matches nothing it shouldn't — but keep prefixes like
# "annotat" open-ended to catch annotator/annotation/annotating.
AI_TRAINING_TITLE_PATTERNS = [
    r"\bai train",              # ai trainer / ai training
    r"\btrainer\b",
    r"annotat",                 # annotator / annotation
    r"\bdata label", r"\blabel(?:l?er|ing)\b",
    r"\brater\b", r"\brating\b",
    r"\btutor\b",
    r"\bhuman data\b",
    r"\brlhf\b",
    r"\bprompt (?:writer|engineer)",
    r"\bevaluat",               # evaluator / evaluation
    r"\bred[- ]team",
    r"\blinguist", r"\blanguage specialist\b",
    r"transcri",                # transcription / transcriber
    r"content moderat",
    r"\bdata collection\b",
    r"\bsearch quality\b",
    r"\btask contributor\b", r"\bcontributor\b",
    r"\bdata operations\b", r"\bdata specialist\b", r"\bdata quality\b",
    r"\bexpert\s*[-–—]",        # "Hardware Architecture Expert - 3P" style
    r"\bsubject matter expert\b",
]
_AI_TITLE_RE = re.compile("|".join(AI_TRAINING_TITLE_PATTERNS), re.IGNORECASE)


def _title_is_ai_training(title: str) -> bool:
    return bool(_AI_TITLE_RE.search(title))


def scrape_ashby_ai(max_results: int = 50) -> list:
    """Scrape Ashby public job boards of AI-training companies."""
    from scraper import JobListing
    jobs = []
    for slug in ASHBY_AI_COMPANIES:
        try:
            url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue

            for posting in resp.json().get("jobs", []):
                title = posting.get("title", "")
                if not title or not _title_is_ai_training(title):
                    continue

                location = posting.get("location", "") or ""
                if posting.get("isRemote"):
                    location = f"Remote — {location}" if location else "Remote"

                salary = ""
                comp = posting.get("compensation") or {}
                if isinstance(comp, dict):
                    salary = comp.get("compensationTierSummary", "") or ""

                jobs.append(JobListing(
                    title=title,
                    company=slug.replace("-", " ").title(),
                    location=location,
                    salary=salary,
                    url=posting.get("jobUrl", "") or posting.get("applyUrl", ""),
                    source="Ashby (AI Training)",
                    date_posted=posting.get("publishedAt", ""),
                    apply_method="📋 Form Fill",
                    role_hint="ai-training",
                ))
                if len(jobs) >= max_results:
                    return jobs

            time.sleep(0.3)
        except Exception as e:
            print(f"    [Ashby/{slug}] Error: {e}")

    print(f"  [Ashby AI] {len(jobs)} AI-training jobs")
    return jobs


def scrape_greenhouse_ai(max_results: int = 50) -> list:
    """Scrape Greenhouse boards of AI-training companies, filtered by title."""
    from scraper import JobListing
    jobs = []
    for slug in GREENHOUSE_AI_COMPANIES:
        try:
            url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue

            for job in resp.json().get("jobs", []):
                title = job.get("title", "")
                if not title or not _title_is_ai_training(title):
                    continue

                loc = job.get("location", {}).get("name", "") if job.get("location") else ""

                jobs.append(JobListing(
                    title=title,
                    company=slug.replace("-", " ").title(),
                    location=loc,
                    url=job.get("absolute_url", ""),
                    source="Greenhouse (AI Training)",
                    date_posted=job.get("updated_at", ""),
                    apply_method="📋 Form Fill",
                    role_hint="ai-training",
                ))
                if len(jobs) >= max_results:
                    return jobs

            time.sleep(0.3)
        except Exception as e:
            print(f"    [Greenhouse-AI/{slug}] Error: {e}")

    print(f"  [Greenhouse AI] {len(jobs)} AI-training jobs")
    return jobs


def scrape_lever_ai(max_results: int = 50) -> list:
    """Scrape Lever boards of AI-training companies, filtered by title."""
    from scraper import JobListing
    jobs = []
    for slug in LEVER_AI_COMPANIES:
        try:
            url = f"https://api.lever.co/v0/postings/{slug}"
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                continue

            for posting in resp.json():
                title = posting.get("text", "")
                if not title or not _title_is_ai_training(title):
                    continue

                loc = posting.get("categories", {}).get("location", "") if posting.get("categories") else ""

                jobs.append(JobListing(
                    title=title,
                    company=slug.replace("-", " ").title(),
                    location=loc,
                    url=posting.get("hostedUrl", ""),
                    source="Lever (AI Training)",
                    description=posting.get("descriptionPlain", "")[:1500],
                    apply_method="📋 Form Fill",
                    role_hint="ai-training",
                ))
                if len(jobs) >= max_results:
                    return jobs

            time.sleep(0.3)
        except Exception as e:
            print(f"    [Lever-AI/{slug}] Error: {e}")

    print(f"  [Lever AI] {len(jobs)} AI-training jobs")
    return jobs


def scrape_ai_training_sources(max_results: int = 50) -> list:
    """Run all AI-training scrapers. Called from run_scrape.py (Step 1c)."""
    all_jobs = []
    seen = set()

    for fn in [scrape_ashby_ai, scrape_greenhouse_ai, scrape_lever_ai]:
        for j in fn(max_results):
            if j.job_id not in seen:
                seen.add(j.job_id)
                all_jobs.append(j)

    print(f"  🤖 AI-training sources: {len(all_jobs)} unique jobs")
    return all_jobs


# ═══════════════════════════════════════════════════════════
# Platform tracker — per-profile signup status persistence
# Stored at output/{profile}/ai_training.json
# ═══════════════════════════════════════════════════════════

TRACKER_STATUSES = ["Not Started", "Signed Up", "Assessment", "Active", "Paused", "Rejected"]


def tracker_path(profile: str) -> Path:
    return _PROJECT_ROOT / "output" / profile / "ai_training.json"


def load_tracker(profile: str) -> dict:
    """Load the per-platform status tracker, seeding missing platforms."""
    path = tracker_path(profile)
    data = {"platforms": {}}
    if path.exists():
        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = {"platforms": {}}

    platforms = data.setdefault("platforms", {})
    for p in AI_TRAINING_PLATFORMS:
        platforms.setdefault(p["id"], {"status": "Not Started", "notes": "", "updated": ""})
    return data


def save_tracker(profile: str, data: dict):
    path = tracker_path(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def update_platform_status(profile: str, platform_id: str, status: str = None, notes: str = None) -> dict:
    data = load_tracker(profile)
    entry = data["platforms"].setdefault(platform_id, {"status": "Not Started", "notes": "", "updated": ""})
    if status is not None:
        entry["status"] = status
    if notes is not None:
        entry["notes"] = notes
    entry["updated"] = datetime.now().strftime("%Y-%m-%d")
    save_tracker(profile, data)
    return entry


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="alex")
    parser.add_argument("--scrape", action="store_true", help="Also test the job-board scrapers")
    args = parser.parse_args()

    print(f"\n🤖 AI Training Platform Directory ({len(AI_TRAINING_PLATFORMS)} platforms)")
    print("=" * 64)
    tracker = load_tracker(args.profile)
    for p in AI_TRAINING_PLATFORMS:
        status = tracker["platforms"].get(p["id"], {}).get("status", "Not Started")
        print(f"\n  {p['name']}  [{p['tier']}]  — {status}")
        print(f"    {p['focus']}")
        print(f"    Pay: {p['pay']}")
        print(f"    Signup: {p['signup']}  →  {p['url']}")
    save_tracker(args.profile, tracker)
    print(f"\n  Tracker saved: {tracker_path(args.profile)}")
    print("\n  ⚠️  All platforms require the task work to be your own — they")
    print("     detect and ban AI-generated submissions.")

    if args.scrape:
        print("\n🔍 Testing job-board scrapers...")
        jobs = scrape_ai_training_sources()
        for j in jobs[:15]:
            print(f"    {j.company}: {j.title} ({j.location or 'n/a'})")
