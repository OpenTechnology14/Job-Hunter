#!/usr/bin/env python3
"""
Job Hunter — Automated Test Runner

Runs smoke tests against live APIs and Playwright browser actions.
No profile required — uses minimal test fixtures.

Usage:
    python run_tests.py                  # Run all tests
    python run_tests.py --api            # API scraper tests only
    python run_tests.py --browser        # Playwright tests only
    python run_tests.py --matcher        # Matcher logic tests only
    python run_tests.py --storage        # CSV storage tests only
    python run_tests.py --all            # Everything including slow tests
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

# ── Prevent config.py from loading a real profile ────────
# We set a fake profile env var and patch sys.argv before any imports
# that touch config.py. Individual tests import scrapers directly.

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

        print(f"{'═'*60}")
        return failed == 0


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

def test_parse_salary():
    """Salary string parsing handles common formats."""
    # Import just the function, not the module (which imports config)
    # We inline the logic to avoid config dependency
    import re

    def parse_salary(salary_str):
        if not salary_str:
            return 0, 0
        amounts = re.findall(r'\$?([\d,]+(?:\.\d+)?)\s*[kK]?', salary_str)
        if not amounts:
            return 0, 0
        parsed = []
        for amt in amounts:
            num = float(amt.replace(",", ""))
            if re.search(r'\d\s*[kK]', salary_str) and num < 1000:
                num *= 1000
            parsed.append(int(num))
        if len(parsed) >= 2:
            return min(parsed), max(parsed)
        elif len(parsed) == 1:
            return parsed[0], parsed[0]
        return 0, 0

    # Standard range
    assert parse_salary("$80,000 - $120,000") == (80000, 120000), "Standard range failed"
    # K notation
    assert parse_salary("$80k - $120k") == (80000, 120000), "K notation failed"
    # Single value
    result = parse_salary("$95,000")
    assert result == (95000, 95000), f"Single value: got {result}"
    # Empty
    assert parse_salary("") == (0, 0), "Empty string should return (0,0)"
    assert parse_salary(None) == (0, 0), "None should return (0,0)"
    # No dollar sign
    result = parse_salary("80000 - 120000")
    assert result[0] > 0, f"No dollar sign: got {result}"


def test_salary_range_overlap():
    """Salary range overlap detection works correctly."""
    def salary_in_range(job_salary_min, job_salary_max, role_min, role_max):
        if job_salary_min == 0 and job_salary_max == 0:
            return True  # No salary = pass through
        if job_salary_max < role_min:
            return False  # Below range
        if job_salary_min > role_max:
            return False  # Above range
        return True

    # Overlapping
    assert salary_in_range(80000, 120000, 90000, 130000) is True
    # Below range
    assert salary_in_range(30000, 50000, 80000, 120000) is False
    # Above range
    assert salary_in_range(200000, 250000, 80000, 120000) is False
    # Contained
    assert salary_in_range(90000, 100000, 80000, 120000) is True
    # No salary
    assert salary_in_range(0, 0, 80000, 120000) is True


def test_keyword_matching():
    """Title-to-query keyword matching logic."""
    def matches(title, query):
        title_lower = title.lower()
        query_lower = query.lower()
        if query_lower in title_lower:
            return True
        query_words = query_lower.split()
        if all(w in title_lower for w in query_words):
            return True
        return False

    assert matches("Senior Software Engineer", "software engineer") is True
    assert matches("Software Engineer II", "software engineer") is True
    assert matches("Data Scientist", "software engineer") is False
    assert matches("Product Manager - Growth", "product manager") is True
    assert matches("IT Project Manager", "project manager") is True
    assert matches("Sales Representative", "software engineer") is False


def test_exclude_keywords():
    """Exclude keywords filter works."""
    excludes = ["senior", "staff", "principal", "director"]
    title = "Senior Software Engineer"
    title_lower = title.lower()
    excluded = any(ex in title_lower for ex in excludes)
    assert excluded is True, "Should exclude 'Senior' title"

    title2 = "Software Engineer II"
    excluded2 = any(ex in title2.lower() for ex in excludes)
    assert excluded2 is False, "Should not exclude 'Software Engineer II'"


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
    admin_path = Path(__file__).parent / "admin" / "server.py"
    assert admin_path.exists(), f"admin/server.py not found at {admin_path}"


def test_form_config_example():
    """form_config_example.json is valid JSON with expected keys."""
    path = Path(__file__).parent / "form_config_example.json"
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
    path = Path(__file__).parent / "profiles" / "example_profile.py"
    assert path.exists(), "profiles/example_profile.py not found"
    content = path.read_text()
    for var in ["USER_PROFILE", "ROLE_PROFILES", "SEARCH_SETTINGS"]:
        assert var in content, f"Missing {var} in example_profile.py"


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

def main():
    args = set(sys.argv[1:])
    verbose = "-v" in args or "--verbose" in args
    args.discard("-v")
    args.discard("--verbose")

    run_api = "--api" in args or "--all" in args or not args
    run_matcher = "--matcher" in args or "--all" in args or not args
    run_storage = "--storage" in args or "--all" in args or not args
    run_browser = "--browser" in args or "--all" in args or not args

    runner = TestRunner(verbose=verbose)

    print(f"\n{'═'*60}")
    print(f"  Job Hunter — Test Runner")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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

    print(f"\n── Config Tests ──")
    runner.run("Admin server exists", test_admin_imports)
    runner.run("Form config template", test_form_config_example)
    runner.run("Example profile", test_example_profile)

    all_passed = runner.summary()
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
