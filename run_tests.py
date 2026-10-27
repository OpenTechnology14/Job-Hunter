#!/usr/bin/env python3
"""
Job Hunter — Automated Test Runner

The default run is offline and deterministic: matcher, storage,
submission-safety and config tests. Live groups (API scrapers, web search,
Playwright browser) run only with --api, --browser or --all.

Every run uses the placeholder profiles/example_profile.py and a temporary
working directory, so it never loads your profile or writes to output/ (JH-002).

Usage:
    python run_tests.py                  # Offline deterministic groups (CI default)
    python run_tests.py --api            # Live API scraper + web-search smoke tests
    python run_tests.py --browser        # Live Playwright tests
    python run_tests.py --matcher        # Matcher logic tests only
    python run_tests.py --storage        # CSV storage tests only
    python run_tests.py --safety         # Submission-safety tests only (offline, fake page)
    python run_tests.py --all            # Every group, offline + live
    python run_tests.py -v               # Verbose output
"""
import sys
import os
import json
import time
import csv
import tempfile
import traceback
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict

# ── Synthetic runtime (JH-002) ───────────────────────────
# Tests never load the operator's profile or write into the repo's output/.
# config.py reads ACTIVE_PROFILE (load_dotenv won't override a set variable)
# and writes output/<profile>/ relative to the working directory, so: force
# the placeholder example profile and run from a throwaway directory.
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ["ACTIVE_PROFILE"] = "example_profile"
TEST_HOME = Path(tempfile.mkdtemp(prefix="jh-tests-"))
os.chdir(TEST_HOME)
import atexit, shutil
atexit.register(shutil.rmtree, TEST_HOME, ignore_errors=True)

# ── Test Infrastructure ──────────────────────────────────

@dataclass
class TestResult:
    name: str
    passed: bool
    duration: float
    message: str = ""
    skipped: bool = False


class TestRunner:
    def __init__(self, verbose: bool = False):
        self.results: list[TestResult] = []
        self.verbose = verbose
        self._start = time.time()

    def run(self, name: str, fn, *args, **kwargs):
        """Run a single test function, catch exceptions."""
        t0 = time.time()
        try:
            fn(*args, **kwargs)
            dt = time.time() - t0
            self.results.append(TestResult(name, True, dt))
            self._print_result("✅", name, dt)
        except SkipTest as e:
            dt = time.time() - t0
            self.results.append(TestResult(name, True, dt, str(e), skipped=True))
            self._print_result("⏭️ ", name, dt, f"SKIP: {e}")
        except AssertionError as e:
            dt = time.time() - t0
            self.results.append(TestResult(name, False, dt, str(e)))
            self._print_result("❌", name, dt, str(e))
            if self.verbose:
                traceback.print_exc()
        except Exception as e:
            dt = time.time() - t0
            self.results.append(TestResult(name, False, dt, f"{type(e).__name__}: {e}"))
            self._print_result("❌", name, dt, f"{type(e).__name__}: {e}")
            if self.verbose:
                traceback.print_exc()
        except SystemExit as e:
            # config.py calls sys.exit(1) when the active profile is missing;
            # record it as a failure instead of aborting the whole run.
            dt = time.time() - t0
            msg = f"SystemExit({e.code}) — likely no profile selected/found (JH-002)"
            self.results.append(TestResult(name, False, dt, msg))
            self._print_result("❌", name, dt, msg)

    def _print_result(self, icon, name, dt, msg=""):
        line = f"  {icon} {name} ({dt:.2f}s)"
        if msg:
            line += f" — {msg}"
        print(line)

    def summary(self):
        total = time.time() - self._start
        passed = sum(1 for r in self.results if r.passed and not r.skipped)
        failed = sum(1 for r in self.results if not r.passed)
        skipped = sum(1 for r in self.results if r.skipped)
        total_count = len(self.results)

        print(f"\n{'═'*60}")
        print(f"  Results: {passed} passed, {failed} failed, {skipped} skipped / {total_count} total")
        print(f"  Time: {total:.1f}s")

        if failed:
            print(f"\n  Failed tests:")
            for r in self.results:
                if not r.passed:
                    print(f"    ❌ {r.name}: {r.message}")

        if total_count == 0:
            print("  ❌ No tests ran — treating as failure (GAP-JH-03).")
        print(f"{'═'*60}")
        return failed == 0 and total_count > 0


class SkipTest(Exception):
    pass


def assert_job_dict(job, source_name):
    """Validate a job dict has all required keys with correct types."""
    required = ["title", "company", "location", "url", "source"]
    for key in required:
        assert key in job, f"Missing key '{key}' in job from {source_name}"
        assert isinstance(job[key], str), f"Key '{key}' should be str, got {type(job[key])} in {source_name}"
    assert job["source"] == source_name, f"Source should be '{source_name}', got '{job['source']}'"
    assert len(job["title"]) > 0, f"Empty title in {source_name} job"
    assert len(job["url"]) > 0, f"Empty URL in {source_name} job"


def assert_job_listing(job, source_name):
    """Validate a JobListing dataclass instance."""
    assert hasattr(job, "title"), f"Missing 'title' attribute in {source_name}"
    assert hasattr(job, "company"), f"Missing 'company' attribute in {source_name}"
    assert hasattr(job, "url"), f"Missing 'url' attribute in {source_name}"
    assert hasattr(job, "source"), f"Missing 'source' attribute in {source_name}"
    assert job.source == source_name, f"Source should be '{source_name}', got '{job.source}'"
    assert len(job.title) > 0, f"Empty title in {source_name}"


# ═══════════════════════════════════════════════════════════
# API Scraper Tests — Live HTTP calls
# ═══════════════════════════════════════════════════════════

def test_himalayas_api():
    """Himalayas API returns valid job listings."""
    import requests
    resp = requests.get(
        "https://himalayas.app/jobs/api/search",
        params={"q": "software engineer", "page": 1, "sort": "recent"},
        headers={"User-Agent": "JobHunterBot/1.0 (test)", "Accept": "application/json"},
        timeout=15,
    )
    assert resp.status_code == 200, f"HTTP {resp.status_code}"
    data = resp.json()
    assert "jobs" in data, f"No 'jobs' key in response. Keys: {list(data.keys())}"
    jobs = data["jobs"]
    assert len(jobs) > 0, "Himalayas returned 0 jobs for 'software engineer'"
    job = jobs[0]
    assert "title" in job, f"No 'title' in job. Keys: {list(job.keys())}"
    assert "companyName" in job, f"No 'companyName' in job"


def test_remoteok_api():
    """RemoteOK API returns valid job data."""
    import requests
    resp = requests.get(
        "https://remoteok.com/api",
        headers={"User-Agent": "JobHunterBot/1.0 (test)", "Accept": "application/json"},
        timeout=15,
    )
    assert resp.status_code == 200, f"HTTP {resp.status_code}"
    data = resp.json()
    assert isinstance(data, list), "RemoteOK should return a list"
    # First item is often a metadata dict, skip it
    job_items = [d for d in data if isinstance(d, dict) and "position" in d]
    assert len(job_items) > 0, "RemoteOK returned 0 job items"
    job = job_items[0]
    assert "position" in job, f"No 'position' in job"
    assert "company" in job, f"No 'company' in job"


def test_greenhouse_api():
    """Greenhouse API returns jobs for a known company slug."""
    import requests
    # Use 'gitlab' — large company, always has postings
    resp = requests.get(
        "https://boards-api.greenhouse.io/v1/boards/gitlab/jobs",
        headers={"User-Agent": "JobHunterBot/1.0 (test)", "Accept": "application/json"},
        timeout=10,
    )
    assert resp.status_code == 200, f"HTTP {resp.status_code}"
    data = resp.json()
    assert "jobs" in data, f"No 'jobs' key. Keys: {list(data.keys())}"
    jobs = data["jobs"]
    assert len(jobs) > 0, "Greenhouse/gitlab returned 0 jobs"
    job = jobs[0]
    assert "title" in job, f"No 'title' in job"
    assert "absolute_url" in job, f"No 'absolute_url' in job"


def test_lever_api():
    """Lever API endpoint responds (companies may have moved off Lever)."""
    import requests
    # Lever API returns 404 when a company slug is invalid or company left Lever.
    # We just verify the endpoint is reachable and responds with valid HTTP.
    slugs = ["anthropic", "netlify", "vercel", "linear", "postman"]
    responded = False
    for slug in slugs:
        try:
            resp = requests.get(
                f"https://api.lever.co/v0/postings/{slug}",
                headers={"User-Agent": "JobHunterBot/1.0 (test)", "Accept": "application/json"},
                timeout=10,
            )
            responded = True
            if resp.status_code == 200:
                data = resp.json()
                assert isinstance(data, list), "Lever should return a list"
                if len(data) > 0:
                    job = data[0]
                    assert "text" in job, f"No 'text' (title) in posting"
                return
        except requests.exceptions.Timeout:
            continue
    if responded:
        # API is reachable but all test slugs are 404 — that's a source issue, not a code bug
        raise SkipTest("Lever API reachable but all test slugs return 404 — companies may have left Lever")
    assert False, "Lever API unreachable for all slugs"


def test_arbeitnow_api():
    """Arbeitnow API returns valid job data."""
    import requests
    resp = requests.get(
        "https://www.arbeitnow.com/api/job-board-api?page=1",
        headers={"User-Agent": "JobHunterBot/1.0 (test)", "Accept": "application/json"},
        timeout=15,
    )
    assert resp.status_code == 200, f"HTTP {resp.status_code}"
    data = resp.json()
    assert "data" in data, f"No 'data' key. Keys: {list(data.keys())}"
    jobs = data["data"]
    assert len(jobs) > 0, "Arbeitnow returned 0 jobs"
    job = jobs[0]
    assert "title" in job, f"No 'title' in job"
    assert "company_name" in job, f"No 'company_name' in job"


def test_usajobs_api():
    """USAJobs API responds (needs API key for real data)."""
    api_key = os.getenv("USAJOBS_API_KEY", "")
    api_email = os.getenv("USAJOBS_EMAIL", "")
    if not api_key or not api_email:
        raise SkipTest("No USAJOBS_API_KEY set")

    import requests
    resp = requests.get(
        "https://data.usajobs.gov/api/search",
        params={"Keyword": "IT specialist", "ResultsPerPage": 5},
        headers={
            "Host": "data.usajobs.gov",
            "User-Agent": api_email,
            "Authorization-Key": api_key,
        },
        timeout=15,
    )
    assert resp.status_code == 200, f"HTTP {resp.status_code}"
    data = resp.json()
    assert "SearchResult" in data, f"No 'SearchResult'. Keys: {list(data.keys())}"


def test_api_response_format_unchanged():
    """Verify API response structures match what scrapers expect.
    Catches silent API changes that return 200 but different JSON shape."""
    import requests
    errors = []

    # Himalayas: expect {jobs: [{title, companyName, slug, ...}]}
    try:
        r = requests.get("https://himalayas.app/jobs/api/search",
                         params={"q": "engineer", "page": 1}, timeout=15)
        if r.status_code == 200:
            d = r.json()
            if "jobs" not in d:
                errors.append("Himalayas: missing 'jobs' key")
            elif d["jobs"] and "companyName" not in d["jobs"][0]:
                errors.append(f"Himalayas: job missing 'companyName'. Keys: {list(d['jobs'][0].keys())}")
    except Exception as e:
        errors.append(f"Himalayas: {e}")

    # Greenhouse: expect {jobs: [{title, absolute_url, location: {name}}]}
    try:
        r = requests.get("https://boards-api.greenhouse.io/v1/boards/gitlab/jobs", timeout=10)
        if r.status_code == 200:
            d = r.json()
            if "jobs" not in d:
                errors.append("Greenhouse: missing 'jobs' key")
            elif d["jobs"] and "absolute_url" not in d["jobs"][0]:
                errors.append(f"Greenhouse: job missing 'absolute_url'. Keys: {list(d['jobs'][0].keys())}")
    except Exception as e:
        errors.append(f"Greenhouse: {e}")

    # RemoteOK: expect [{position, company, url, ...}]
    try:
        r = requests.get("https://remoteok.com/api", timeout=15)
        if r.status_code == 200:
            d = r.json()
            items = [x for x in d if isinstance(x, dict) and "position" in x]
            if not items:
                errors.append("RemoteOK: no items with 'position' key")
    except Exception as e:
        errors.append(f"RemoteOK: {e}")

    assert not errors, "API format changes detected:\n  " + "\n  ".join(errors)


# ═══════════════════════════════════════════════════════════
# Matcher Tests — Pure logic, no network
# ═══════════════════════════════════════════════════════════

class _patched:
    """Temporarily set module attributes (e.g. matcher.ROLE_PROFILES)."""

    def __init__(self, module, **attrs):
        self.module, self.attrs, self.saved = module, attrs, {}

    def __enter__(self):
        for k, v in self.attrs.items():
            self.saved[k] = getattr(self.module, k)
            setattr(self.module, k, v)
        return self.module

    def __exit__(self, *exc):
        for k, v in self.saved.items():
            setattr(self.module, k, v)


SYNTHETIC_ROLES = {
    "swe": {"label": "Software Engineer", "search_queries": ["software engineer"],
            "salary_min": 80000, "salary_max": 120000, "resume_file": "swe.pdf"},
    "pm": {"label": "Project Manager", "search_queries": ["project manager", "product manager"],
           "salary_min": 70000, "salary_max": 110000, "resume_file": "pm.pdf"},
}


def test_parse_salary():
    """matcher.parse_salary handles common formats (production function, JH-014)."""
    from matcher import parse_salary
    assert parse_salary("$80,000 - $120,000") == (80000, 120000), "Standard range failed"
    assert parse_salary("$80k - $120k") == (80000, 120000), "K notation failed"
    result = parse_salary("$95,000")
    assert result == (95000, 95000), f"Single value: got {result}"
    assert parse_salary("") == (0, 0), "Empty string should return (0,0)"
    assert parse_salary(None) == (0, 0), "None should return (0,0)"
    result = parse_salary("80000 - 120000")
    assert result[0] > 0, f"No dollar sign: got {result}"


def test_salary_range_overlap():
    """matcher.salary_in_range overlap rules (production function, JH-014)."""
    from matcher import salary_in_range
    assert salary_in_range("$80,000 - $120,000", 90000, 130000)[0] is True, "Overlap"
    assert salary_in_range("$30,000 - $50,000", 80000, 120000)[0] is False, "Below range"
    assert salary_in_range("$200,000 - $250,000", 80000, 120000)[0] is False, "Above range"
    assert salary_in_range("$90,000 - $100,000", 80000, 120000)[0] is True, "Inside range"
    ok, reason = salary_in_range("", 80000, 120000)
    assert ok is True and "No salary" in reason, f"No salary should pass through: {reason}"


def test_keyword_matching():
    """matcher.match_title_to_role against synthetic roles (production function, JH-014)."""
    import matcher
    with _patched(matcher, ROLE_PROFILES=SYNTHETIC_ROLES):
        role = lambda t: matcher.match_title_to_role(t)[0]
        assert role("Senior Software Engineer") == "swe"
        assert role("Software Engineer II") == "swe"
        assert role("Product Manager - Growth") == "pm"
        assert role("IT Project Manager") == "pm"
        assert role("Data Scientist") == "", "Unrelated title must not match"
        assert role("Sales Representative") == "", "Unrelated title must not match"


def test_exclude_keywords():
    """matcher.match_jobs drops titles with exclude_keywords (production function, JH-014)."""
    import matcher
    settings = {"exclude_keywords": ["senior", "staff", "principal", "director"]}
    with _patched(matcher, ROLE_PROFILES=SYNTHETIC_ROLES, SEARCH_SETTINGS=settings):
        out = matcher.match_jobs([
            {"title": "Senior Software Engineer", "salary": "", "url": "u1"},
            {"title": "Software Engineer II", "salary": "", "url": "u2"},
        ])
    titles = [j["title"] for j in out]
    assert "Senior Software Engineer" not in titles, "Should exclude 'Senior' title"
    assert "Software Engineer II" in titles, "Should keep 'Software Engineer II'"
    assert out[0]["role_category"] == "swe", f"Wrong role: {out[0].get('role_category')}"


# ═══════════════════════════════════════════════════════════
# CSV Storage Tests — File I/O with temp files
# ═══════════════════════════════════════════════════════════

SHEET_COLUMNS = [
    "Job Title", "Company", "Location", "Work Type", "Salary",
    "Role Category", "Match Reason", "Apply Method", "Apply",
    "Resume Version", "URL", "Source", "Date Posted", "Date Found",
    "Date Applied", "Notes",
]


def test_csv_write_read():
    """Write jobs to CSV and read them back."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        tmppath = f.name
        writer = csv.DictWriter(f, fieldnames=SHEET_COLUMNS)
        writer.writeheader()
        writer.writerow({
            "Job Title": "Software Engineer",
            "Company": "TestCorp",
            "Location": "Remote",
            "Work Type": "Remote",
            "Salary": "$100,000 - $130,000",
            "Role Category": "engineering",
            "Match Reason": "Keyword match",
            "Apply Method": "Form Fill",
            "Apply": "",
            "Resume Version": "software_engineer.pdf",
            "URL": "https://example.com/job/123",
            "Source": "Greenhouse",
            "Date Found": "2026-05-20",
            "Date Applied": "",
            "Notes": "",
        })

    try:
        with open(tmppath, newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
        assert rows[0]["Job Title"] == "Software Engineer"
        assert rows[0]["Company"] == "TestCorp"
        assert rows[0]["URL"] == "https://example.com/job/123"
    finally:
        os.unlink(tmppath)


def test_csv_dedup():
    """Duplicate URLs should not be appended."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        tmppath = f.name
        writer = csv.DictWriter(f, fieldnames=SHEET_COLUMNS)
        writer.writeheader()
        row = {col: "" for col in SHEET_COLUMNS}
        row["URL"] = "https://example.com/job/123"
        row["Job Title"] = "Engineer"
        writer.writerow(row)

    try:
        # Read existing URLs
        with open(tmppath, newline="") as f:
            existing_urls = {r["URL"] for r in csv.DictReader(f)}

        # Try to append duplicate
        new_url = "https://example.com/job/123"
        assert new_url in existing_urls, "URL should already exist"

        # Append a new unique URL
        new_url2 = "https://example.com/job/456"
        assert new_url2 not in existing_urls, "New URL should not exist yet"

        with open(tmppath, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=SHEET_COLUMNS)
            if new_url2 not in existing_urls:
                row2 = {col: "" for col in SHEET_COLUMNS}
                row2["URL"] = new_url2
                row2["Job Title"] = "Manager"
                writer.writerow(row2)

        with open(tmppath, newline="") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 2, f"Expected 2 rows after dedup append, got {len(rows)}"
    finally:
        os.unlink(tmppath)


def test_csv_column_order():
    """CSV columns match expected order."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        tmppath = f.name
        writer = csv.DictWriter(f, fieldnames=SHEET_COLUMNS)
        writer.writeheader()

    try:
        with open(tmppath) as f:
            header = f.readline().strip()
        expected = ",".join(SHEET_COLUMNS)
        assert header == expected, f"Column order mismatch:\n  Got:      {header}\n  Expected: {expected}"
    finally:
        os.unlink(tmppath)


def test_stale_cleanup():
    """Stale job cleanup uses Date Posted (3 weeks), falls back to Date Found."""
    from datetime import timedelta

    stale_date = (datetime.now() - timedelta(days=25)).strftime("%Y-%m-%d")  # > 21 days
    recent_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
    borderline_date = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")  # < 21 days

    rows = [
        # Date Posted is primary — stale posting date triggers removal
        {"Job Title": "Old Posted Blank", "Apply": "", "Date Posted": stale_date, "Date Found": recent_date},
        {"Job Title": "Old Posted N", "Apply": "N", "Date Posted": stale_date, "Date Found": recent_date},
        # Approved/Done are never removed even with stale Date Posted
        {"Job Title": "Old Posted Y", "Apply": "Y", "Date Posted": stale_date, "Date Found": stale_date},
        {"Job Title": "Old Posted Done", "Apply": "Done", "Date Posted": stale_date, "Date Found": stale_date},
        # Recent Date Posted keeps the job even if Date Found is old
        {"Job Title": "Recent Posted", "Apply": "", "Date Posted": recent_date, "Date Found": stale_date},
        # Borderline — 20 days < 21 day cutoff → keep
        {"Job Title": "Borderline Posted", "Apply": "", "Date Posted": borderline_date, "Date Found": stale_date},
        # No Date Posted → falls back to Date Found
        {"Job Title": "Fallback Old", "Apply": "", "Date Posted": "", "Date Found": stale_date},
        {"Job Title": "Fallback Recent", "Apply": "", "Date Posted": "", "Date Found": recent_date},
        # No dates at all → keep (legacy data)
        {"Job Title": "No Date", "Apply": "", "Date Posted": "", "Date Found": ""},
    ]

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        tmppath = f.name
        writer = csv.DictWriter(f, fieldnames=SHEET_COLUMNS)
        writer.writeheader()
        for r in rows:
            full = {col: "" for col in SHEET_COLUMNS}
            full.update(r)
            writer.writerow(full)

    try:
        # Apply cleanup logic (inline, mirrors local_sync.cleanup_stale_jobs)
        with open(tmppath, newline="") as f:
            all_rows = list(csv.DictReader(f))

        cutoff = datetime.now() - timedelta(days=21)
        keep = []
        removed = 0
        for row in all_rows:
            apply_val = (row.get("Apply", "") or "").strip().upper()
            if apply_val in ("Y", "DONE") or apply_val.startswith("DONE"):
                keep.append(row)
                continue
            # Use Date Posted first, fall back to Date Found
            date_str = (row.get("Date Posted", "") or "").strip()
            if not date_str:
                date_str = (row.get("Date Found", "") or "").strip()
            if not date_str:
                keep.append(row)
                continue
            try:
                job_date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                keep.append(row)
                continue
            if job_date < cutoff:
                removed += 1
            else:
                keep.append(row)

        assert removed == 3, f"Should remove 3 stale jobs, removed {removed}"
        assert len(keep) == 6, f"Should keep 6 jobs, kept {len(keep)}"

        kept_titles = [r["Job Title"] for r in keep]
        # Approved/Done always kept
        assert "Old Posted Y" in kept_titles, "Approved job should be kept"
        assert "Old Posted Done" in kept_titles, "Done job should be kept"
        # Recent Date Posted keeps job
        assert "Recent Posted" in kept_titles, "Recent posted job should be kept"
        # Borderline (20 days < 21 cutoff) should be kept
        assert "Borderline Posted" in kept_titles, "Borderline job should be kept"
        # Fallback to Date Found — recent stays, old goes
        assert "Fallback Recent" in kept_titles, "Recent fallback should be kept"
        assert "Fallback Old" not in kept_titles, "Old fallback should be removed"
        # No date → legacy keep
        assert "No Date" in kept_titles, "No-date job should be kept"
        # Stale unapproved removed
        assert "Old Posted Blank" not in kept_titles, "Old stale unapproved should be removed"
        assert "Old Posted N" not in kept_titles, "Old stale rejected should be removed"
    finally:
        os.unlink(tmppath)


def test_web_search_url_detection():
    """Web search URL detection identifies job URLs correctly."""
    from scraper_web import _is_job_url, _extract_company_from_url

    # Should detect as job URLs
    assert _is_job_url("https://boards.greenhouse.io/stripe/jobs/123")
    assert _is_job_url("https://jobs.lever.co/anthropic/abc")
    assert _is_job_url("https://example.com/careers/engineer")
    assert _is_job_url("https://indeed.com/viewjob?jk=abc")

    # Should NOT detect as job URLs
    assert not _is_job_url("https://nytimes.com/article/layoffs")
    assert not _is_job_url("https://blog.example.com/hiring-tips")

    # Company extraction
    assert _extract_company_from_url("https://boards.greenhouse.io/stripe/jobs/1") == "Stripe"
    assert _extract_company_from_url("https://jobs.lever.co/anthropic/x") == "Anthropic"
    assert _extract_company_from_url("https://careers.google.com/jobs") == "Google"


def test_web_search_duckduckgo():
    """DuckDuckGo search returns results (free, no API key)."""
    from scraper_web import _search_duckduckgo
    results = _search_duckduckgo('"software engineer" job remote', max_results=5)
    assert len(results) > 0, "DuckDuckGo returned 0 results"
    assert "url" in results[0], "Result missing 'url' key"
    assert "title" in results[0], "Result missing 'title' key"


# ═══════════════════════════════════════════════════════════
# Playwright Browser Tests — Real browser actions
# ═══════════════════════════════════════════════════════════

def test_playwright_installed():
    """Playwright can be imported and Chromium is available."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("about:blank")
        assert page.url == "about:blank"
        browser.close()


def test_playwright_navigation():
    """Browser can navigate to a real page and read the title."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://httpbin.org/html", timeout=15000)
        assert "Herman Melville" in page.content() or page.title() != ""
        browser.close()


def test_playwright_form_detection():
    """Browser can detect form elements on a test page."""
    from playwright.sync_api import sync_playwright

    html = """
    <html><body>
        <form>
            <label for="name">Full Name</label>
            <input type="text" id="name" name="name">
            <label for="email">Email</label>
            <input type="email" id="email" name="email">
            <label for="phone">Phone</label>
            <input type="tel" id="phone" name="phone">
            <input type="file" id="resume" name="resume">
            <select id="country" name="country">
                <option value="us">United States</option>
                <option value="uk">United Kingdom</option>
            </select>
            <button type="submit">Apply</button>
        </form>
    </body></html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html)

        # Find text inputs
        inputs = page.query_selector_all("input:visible")
        assert len(inputs) >= 3, f"Expected 3+ inputs, found {len(inputs)}"

        # Find file input
        file_inputs = page.query_selector_all('input[type="file"]')
        assert len(file_inputs) == 1, "Should find 1 file input"

        # Find select
        selects = page.query_selector_all("select:visible")
        assert len(selects) == 1, "Should find 1 select"

        # Find submit button
        buttons = page.query_selector_all('button[type="submit"]')
        assert len(buttons) == 1, "Should find 1 submit button"

        browser.close()


def test_playwright_form_fill():
    """Browser can fill form fields programmatically."""
    from playwright.sync_api import sync_playwright

    html = """
    <html><body>
        <form>
            <input type="text" id="name" name="name">
            <input type="email" id="email" name="email">
            <input type="tel" id="phone" name="phone">
            <select id="exp" name="experience">
                <option value="">Select</option>
                <option value="3">3 years</option>
                <option value="5">5 years</option>
            </select>
        </form>
    </body></html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html)

        # Fill text fields
        page.fill("#name", "Test User")
        page.fill("#email", "test@example.com")
        page.fill("#phone", "555-0100")

        # Verify fills
        assert page.input_value("#name") == "Test User"
        assert page.input_value("#email") == "test@example.com"
        assert page.input_value("#phone") == "555-0100"

        # Select dropdown
        page.select_option("#exp", "5")
        assert page.input_value("#exp") == "5"

        browser.close()


def test_playwright_file_upload():
    """Browser can set a file on a file input element."""
    from playwright.sync_api import sync_playwright

    # Create a temp file to "upload"
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4 test")
        tmppath = f.name

    html = '<html><body><input type="file" id="resume" accept=".pdf"></body></html>'

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content(html)

            file_input = page.query_selector('#resume')
            file_input.set_input_files(tmppath)

            # Verify file was attached (check via JS)
            file_count = page.evaluate("document.querySelector('#resume').files.length")
            assert file_count == 1, f"Expected 1 file, got {file_count}"

            browser.close()
    finally:
        os.unlink(tmppath)


def test_playwright_apply_type_detection():
    """Apply type detection logic works on test HTML."""
    # Test the detection patterns without importing browser_apply.py
    import re

    def detect_apply_type(content, url):
        content = content.lower()
        url = url.lower()
        if any(x in content for x in ["easy apply", "easyapply", "quick apply"]):
            return "easy-apply"
        if any(x in content for x in ['type="file"', "upload resume", "attach resume"]):
            return "resume-upload"
        if "greenhouse.io" in url or "lever.co" in url:
            return "form-fill"
        if any(x in content for x in ["application form", "apply now"]):
            return "form-fill"
        return "manual"

    assert detect_apply_type("Click Easy Apply to submit", "https://linkedin.com") == "easy-apply"
    assert detect_apply_type('<input type="file">', "https://example.com") == "resume-upload"
    assert detect_apply_type("Some job page", "https://boards.greenhouse.io/company") == "form-fill"
    assert detect_apply_type("Click Apply Now", "https://example.com") == "form-fill"
    assert detect_apply_type("View job description", "https://example.com") == "manual"


def test_playwright_field_pattern_matching():
    """Field pattern regex matching works for common form labels."""
    import re

    FIELD_PATTERNS = {
        r"first.?name": "first_name",
        r"last.?name": "last_name",
        r"full.?name": "full_name",
        r"^name$": "full_name",
        r"email": "email",
        r"phone|mobile|tel": "phone",
        r"linkedin": "linkedin",
        r"website|portfolio|url|blog": "website",
        r"city|location": "city",
        r"state": "state",
        r"country": "country",
        r"current.?(company|employer|org)": "current_company",
        r"current.?(title|role|position)": "current_title",
        r"years?.?(of)?.?experience": "years_experience",
    }

    test_cases = [
        ("first name", "first_name"),
        ("first_name", "first_name"),
        ("last name", "last_name"),
        ("email address", "email"),
        ("phone number", "phone"),
        ("mobile number", "phone"),
        ("linkedin profile", "linkedin"),
        ("portfolio url", "website"),
        ("city", "city"),
        ("current company", "current_company"),
        ("years of experience", "years_experience"),
    ]

    for label, expected_key in test_cases:
        matched = None
        for pattern, key in FIELD_PATTERNS.items():
            if re.search(pattern, label.lower()):
                matched = key
                break
        assert matched == expected_key, f"Label '{label}' matched '{matched}', expected '{expected_key}'"


# ═══════════════════════════════════════════════════════════
# Admin Panel Tests — Server response checks
# ═══════════════════════════════════════════════════════════

def test_admin_imports():
    """Admin server module can be imported."""
    admin_path = ROOT / "admin" / "server.py"
    assert admin_path.exists(), f"admin/server.py not found at {admin_path}"


def test_form_config_example():
    """form_config_example.json is valid JSON with expected keys."""
    path = ROOT / "form_config_example.json"
    if not path.exists():
        raise SkipTest("form_config_example.json not found")
    with open(path) as f:
        data = json.load(f)
    assert "custom_fields" in data, "Missing 'custom_fields' key"
    assert "select_defaults" in data, "Missing 'select_defaults' key"
    assert isinstance(data["custom_fields"], list), "custom_fields should be a list"
    assert isinstance(data["select_defaults"], list), "select_defaults should be a list"


def test_example_profile():
    """example_profile.py exists and has required variables."""
    path = ROOT / "profiles" / "example_profile.py"
    assert path.exists(), "profiles/example_profile.py not found"
    content = path.read_text()
    for var in ["USER_PROFILE", "ROLE_PROFILES", "SEARCH_SETTINGS"]:
        assert var in content, f"Missing {var} in example_profile.py"


# ═══════════════════════════════════════════════════════════
# Submission Safety Tests (offline — fake page, no browser, no profile)
# GAP-JH-04 / OTJ-07 in docs/proposals/PROPOSAL_RELEASE_AND_SAFETY_GAP_CLOSURE.md
# ═══════════════════════════════════════════════════════════

class _FakeButton:
    def __init__(self, page, label):
        self.page = page
        self.label = label

    def click(self):
        self.page.clicks.append(self.label)
        self.page.on_click(self.label)

    def get_attribute(self, name):
        return self.label if name == "aria-label" else None

    def inner_text(self):
        return self.label


class _FakeApplyPage:
    """Easy Apply flow: entry button, then a sequence of step buttons.

    Each click on a step button advances to the next; the last step is
    the Submit button. Records every click so tests can assert on them.
    """

    def __init__(self, steps):
        self.clicks = []
        self.steps = list(steps)
        self.entry = _FakeButton(self, "Easy Apply")
        self.step_index = None  # None until the entry button is clicked

    def on_click(self, label):
        if label == "Easy Apply":
            self.step_index = 0
        elif self.step_index is not None:
            self.step_index += 1

    def query_selector(self, selector):
        if "jobs-apply-button" in selector:
            return self.entry
        if self.step_index is not None and self.step_index < len(self.steps):
            return _FakeButton(self, self.steps[self.step_index])
        return None

    def query_selector_all(self, selector):
        return []


def _import_browser_apply_isolated():
    """Import browser_apply with stub config/storage/resume modules.

    browser_apply reads config at import time (which would load the active
    profile and write into output/). Stubbing keeps this test synthetic:
    no profile, no personal data, temp directory only.
    """
    try:
        import playwright.sync_api  # noqa: F401 — browser_apply imports Page from it
    except ImportError:
        raise SkipTest("playwright not installed")
    import types
    import importlib

    tmp = Path(tempfile.mkdtemp(prefix="jh-safety-"))
    atexit.register(shutil.rmtree, tmp, ignore_errors=True)
    stubs = {
        "config": types.SimpleNamespace(
            USER_PROFILE={"name": "Test Person", "email": "test@example.com"},
            ROLE_PROFILES={},
            PROFILE_DIR=tmp,
        ),
        "resume_picker": types.SimpleNamespace(get_resume_by_filename=lambda f: ""),
        "storage": types.SimpleNamespace(
            get_worksheet=lambda: None,
            pull_ready_jobs=lambda ws: [],
            mark_applied=lambda *a, **k: None,
        ),
    }
    saved = {name: sys.modules.get(name) for name in [*stubs, "browser_apply"]}
    try:
        for name, mod in stubs.items():
            sys.modules[name] = mod
        sys.modules.pop("browser_apply", None)
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            ba = importlib.import_module("browser_apply")
    finally:
        for name, mod in saved.items():
            if mod is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = mod
    ba.time.sleep = lambda s: None
    return ba


def _run_quietly(fn, answers, *args, **kwargs):
    """Call fn with input() answering from `answers`; returns (result, prompts)."""
    import builtins, io, contextlib
    prompts = []
    queue = list(answers)

    def fake_input(prompt=""):
        prompts.append(prompt)
        return queue.pop(0) if queue else ""

    original = builtins.input
    builtins.input = fake_input
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            result = fn(*args, **kwargs)
    finally:
        builtins.input = original
    return result, prompts


def test_dry_run_easy_apply_never_clicks_submit():
    """GAP-JH-04: dry-run reaches a visible Submit button and does not click it."""
    ba = _import_browser_apply_isolated()
    page = _FakeApplyPage(["Continue to next step", "Review your application", "Submit application"])
    result, _ = _run_quietly(ba.handle_easy_apply, [""], page, "", dry_run=True)
    assert result is False, "dry-run must not report a submission"
    assert page.step_index == 2, f"flow should reach the Submit step, stopped at {page.step_index}"
    assert "Submit application" not in page.clicks, f"dry-run clicked Submit: {page.clicks}"


def test_dry_run_form_apply_clicks_nothing():
    """GAP-JH-04: generic form path in dry-run clicks nothing and reports no submission."""
    ba = _import_browser_apply_isolated()
    page = _FakeApplyPage(["Submit application"])
    page.step_index = 0  # Submit visible immediately
    result, _ = _run_quietly(ba.handle_form_apply, [""], page, "", dry_run=True)
    assert result is False, "dry-run must not report a submission"
    assert page.clicks == [], f"dry-run clicked: {page.clicks}"


def test_live_submit_requires_explicit_confirmation():
    """Live mode: skipping at the SUBMIT prompt clicks nothing; confirming clicks Submit exactly once."""
    ba = _import_browser_apply_isolated()

    skipped = _FakeApplyPage(["Submit application"])
    result, prompts = _run_quietly(ba.handle_easy_apply, ["", "s"], skipped, "", dry_run=False)
    assert result is False and "Submit application" not in skipped.clicks, \
        f"skip at SUBMIT prompt still submitted: {skipped.clicks}"
    assert any("SUBMIT" in p for p in prompts), "no SUBMIT confirmation prompt was shown"

    confirmed = _FakeApplyPage(["Submit application"])
    result, _ = _run_quietly(ba.handle_easy_apply, ["", ""], confirmed, "", dry_run=False)
    assert result is True, "confirmed submit should report success"
    assert confirmed.clicks.count("Submit application") == 1, f"clicks: {confirmed.clicks}"


def _run_isolated_python(code, extra_env=None):
    """Run `code` in a fresh interpreter with no profile selected, cwd in a temp dir."""
    import subprocess
    root = ROOT
    env = {**os.environ, "ACTIVE_PROFILE": "", "PYTHONPATH": str(root)}
    env.update(extra_env or {})
    cwd = tempfile.mkdtemp(prefix="jh-iso-")
    atexit.register(shutil.rmtree, cwd, ignore_errors=True)
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True,
                          text=True, timeout=60, cwd=cwd, env=env)
    return proc, Path(cwd)


def test_no_profile_gives_clear_error():
    """JH-016: no --profile and no ACTIVE_PROFILE -> clear error, exit 1, no output/ created."""
    proc, cwd = _run_isolated_python("import config")
    out = proc.stdout + proc.stderr
    assert proc.returncode == 1, f"expected exit 1, got {proc.returncode}: {out[-300:]}"
    assert "No profile selected" in out, f"unclear error: {out[-300:]}"
    assert "--profile" in out and "ACTIVE_PROFILE" in out, "error must name both ways to select a profile"
    assert "Example" not in out, "error still references the nonexistent 'Example' default"
    assert not (cwd / "output").exists(), "config created output/ before failing"


def test_generate_resume_route_gone():
    """JH-015: the removed resume generator's route answers 410, never spawns a process."""
    code = (
        "import sys, json; sys.path.insert(0, 'admin'); import server\n"
        "import subprocess\n"
        "subprocess.run = lambda *a, **k: (_ for _ in ()).throw(AssertionError('spawned'))\n"
        "c = server.app.test_client()\n"
        "r = c.post('/api/ai-training/someone/generate-resume')\n"
        "print(json.dumps({'status': r.status_code, 'body': r.get_json()}))\n"
    )
    root = ROOT
    proc, _ = _run_isolated_python(code, {"PYTHONPATH": str(root) + os.pathsep + str(root / "admin")})
    if "No module named 'flask'" in proc.stderr:
        raise SkipTest("flask not installed")
    assert proc.returncode == 0, f"server import/request failed: {proc.stderr[-400:]}"
    result = json.loads(proc.stdout.strip().splitlines()[-1])
    assert result["status"] == 410, f"expected 410 Gone, got {result}"
    assert "Resumes page" in (result["body"] or {}).get("error", ""), f"unhelpful error: {result}"


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

def main():
    args = set(sys.argv[1:])
    verbose = "-v" in args or "--verbose" in args
    args.discard("-v")
    args.discard("--verbose")

    # No flags = offline deterministic groups only (JH-005). Live groups are opt-in.
    run_api = "--api" in args or "--all" in args
    run_matcher = "--matcher" in args or "--all" in args or not args
    run_storage = "--storage" in args or "--all" in args or not args
    run_browser = "--browser" in args or "--all" in args
    run_safety = "--safety" in args or "--all" in args or not args

    runner = TestRunner(verbose=verbose)

    print(f"\n{'═'*60}")
    print(f"  Job Hunter — Test Runner")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Profile: example_profile (synthetic) · cwd: {TEST_HOME}")
    if not (run_api or run_browser):
        print("  Live groups skipped (use --api, --browser or --all)")
    print(f"{'═'*60}")

    if run_api:
        print(f"\n── API Scraper Tests (live HTTP) ──")
        runner.run("Himalayas API", test_himalayas_api)
        runner.run("RemoteOK API", test_remoteok_api)
        runner.run("Greenhouse API", test_greenhouse_api)
        runner.run("Lever API", test_lever_api)
        runner.run("Arbeitnow API", test_arbeitnow_api)
        runner.run("USAJobs API", test_usajobs_api)
        runner.run("API format stability", test_api_response_format_unchanged)

    if run_matcher:
        print(f"\n── Matcher Tests ──")
        runner.run("Parse salary strings", test_parse_salary)
        runner.run("Salary range overlap", test_salary_range_overlap)
        runner.run("Keyword matching", test_keyword_matching)
        runner.run("Exclude keywords", test_exclude_keywords)

    if run_storage:
        print(f"\n── Storage Tests ──")
        runner.run("CSV write/read", test_csv_write_read)
        runner.run("CSV dedup", test_csv_dedup)
        runner.run("CSV column order", test_csv_column_order)
        runner.run("Stale job cleanup", test_stale_cleanup)

    if run_api:
        print(f"\n── Web Search Tests ──")
        runner.run("URL detection", test_web_search_url_detection)
        runner.run("DuckDuckGo search", test_web_search_duckduckgo)

    if run_browser:
        print(f"\n── Browser Tests (Playwright) ──")
        runner.run("Playwright installed", test_playwright_installed)
        runner.run("Page navigation", test_playwright_navigation)
        runner.run("Form detection", test_playwright_form_detection)
        runner.run("Form fill", test_playwright_form_fill)
        runner.run("File upload", test_playwright_file_upload)
        runner.run("Apply type detection", test_playwright_apply_type_detection)
        runner.run("Field pattern matching", test_playwright_field_pattern_matching)

    if run_safety:
        print(f"\n── Submission Safety Tests (offline) ──")
        runner.run("Dry-run Easy Apply never clicks Submit", test_dry_run_easy_apply_never_clicks_submit)
        runner.run("Dry-run form apply clicks nothing", test_dry_run_form_apply_clicks_nothing)
        runner.run("Live submit needs explicit confirmation", test_live_submit_requires_explicit_confirmation)

    print(f"\n── Config Tests ──")
    runner.run("Admin server exists", test_admin_imports)
    runner.run("Form config template", test_form_config_example)
    runner.run("Example profile", test_example_profile)
    runner.run("No profile -> clear error (JH-016)", test_no_profile_gives_clear_error)
    runner.run("Generate-resume route is 410 (JH-015)", test_generate_resume_route_gone)

    all_passed = runner.summary()
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
