"""
Browser Apply
Reads jobs marked "Ready to Apply" from the Google Sheet,
opens Playwright browser, picks the right resume, and applies.

Always supervised — browser is visible, pauses before submit.

Usage:
    python run_apply.py --profile alex
    python run_apply.py --profile alex --dry-run
"""
import json
import re
import time
import argparse
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, Page

from config import USER_PROFILE, ROLE_PROFILES, PROFILE_DIR
from resume_picker import get_resume_by_filename
from storage import get_worksheet, pull_ready_jobs, mark_applied


# ── Autofill Data ─────────────────────────────────────────

AUTOFILL_DATA = {
    "first_name": USER_PROFILE["name"].split()[0],
    "last_name": USER_PROFILE["name"].split()[-1],
    "full_name": USER_PROFILE["name"],
    "email": USER_PROFILE.get("email", ""),
    "phone": USER_PROFILE.get("phone", ""),
    "linkedin": USER_PROFILE.get("linkedin", ""),
    "website": USER_PROFILE["portfolio_urls"][0] if USER_PROFILE.get("portfolio_urls") else "",
    "city": USER_PROFILE.get("city", ""),
    "state": USER_PROFILE.get("state", ""),
    "country": USER_PROFILE.get("country", "United States"),
    "current_company": USER_PROFILE.get("current_role", "").split(" @ ")[-1] if " @ " in USER_PROFILE.get("current_role", "") else "",
    "current_title": USER_PROFILE.get("current_role", "").split(" @ ")[0] if " @ " in USER_PROFILE.get("current_role", "") else USER_PROFILE.get("current_role", ""),
    "years_experience": str(USER_PROFILE.get("experience_years", "")),
}

# Standard field patterns (built-in)
FIELD_PATTERNS = {
    r"first.?name": "first_name",
    r"last.?name": "last_name",
    r"full.?name": "full_name",
    r"^name$": "full_name",
    r"email": "email",
    r"phone|mobile|tel": "phone",
    r"linkedin": "linkedin",
    r"website|portfolio|url|blog": "website",
    # Word-bounded so "relocation" / "current location?" in a screener
    # question can't pull the city value into the wrong box.
    r"\bcity\b|\blocation\b": "city",
    r"\bstate\b|province": "state",
    r"\bcountry\b": "country",
    r"current.?(company|employer|org)": "current_company",
    r"current.?(title|role|position)": "current_title",
    r"years?.?(of)?.?experience": "years_experience",
}


def _is_screener_question(identifier: str) -> bool:
    """
    True when a field's identifier reads like a free-text screener/EEO
    question rather than a short labelled identity field ("City", "Email").

    Why this matters: built-in identity patterns are matched with an
    unanchored re.search against the whole label, so a long question like
    "Will you require sponsorship for a visa at your current location?"
    would substring-match `location` and dump the city value into it.
    Real identity fields have short labels; questions are long and/or end
    in "?". For those we skip the greedy identity autofill and only apply
    the explicit, intentional custom rules from form_config.json.
    """
    ident = identifier.strip()
    return "?" in ident or len(ident.split()) > 7

# ── Load custom form config ──────────────────────────────

FORM_CONFIG_PATH = PROFILE_DIR / "form_config.json"
CUSTOM_FIELDS = []
SELECT_DEFAULTS = []

if FORM_CONFIG_PATH.exists():
    try:
        with open(FORM_CONFIG_PATH) as _f:
            _form_cfg = json.load(_f)
        CUSTOM_FIELDS = _form_cfg.get("custom_fields", [])
        SELECT_DEFAULTS = _form_cfg.get("select_defaults", [])
        print(f"  📝 Form config loaded: {len(CUSTOM_FIELDS)} custom fields, {len(SELECT_DEFAULTS)} select defaults")
    except Exception as _e:
        print(f"  ⚠️  Form config error: {_e}")
else:
    # Create default from example if it doesn't exist
    example = Path(__file__).parent / "form_config_example.json"
    if example.exists():
        import shutil
        shutil.copy(example, FORM_CONFIG_PATH)
        print(f"  📝 Created form config: {FORM_CONFIG_PATH}")
        with open(FORM_CONFIG_PATH) as _f:
            _form_cfg = json.load(_f)
        CUSTOM_FIELDS = _form_cfg.get("custom_fields", [])
        SELECT_DEFAULTS = _form_cfg.get("select_defaults", [])


# ── Page Helpers ──────────────────────────────────────────

def detect_apply_type(page: Page) -> str:
    content = page.content().lower()
    url = page.url.lower()

    if any(x in content for x in ["easy apply", "easyapply", "quick apply"]):
        return "easy-apply"
    if any(x in content for x in ['type="file"', "upload resume", "attach resume"]):
        return "resume-upload"
    if "greenhouse.io" in url or "lever.co" in url:
        return "form-fill"
    if any(x in content for x in ["application form", "apply now"]):
        return "form-fill"
    return "manual"


def fill_form_fields(page: Page):
    inputs = page.query_selector_all("input:visible, textarea:visible")
    for inp in inputs:
        input_type = inp.get_attribute("type") or "text"
        if input_type in ("file", "hidden", "submit", "button", "checkbox", "radio"):
            continue
        current = inp.input_value()
        if current and len(current) > 2:
            continue

        input_id = inp.get_attribute("id") or ""
        input_name = inp.get_attribute("name") or ""
        placeholder = inp.get_attribute("placeholder") or ""
        aria_label = inp.get_attribute("aria-label") or ""

        label_text = ""
        if input_id:
            label_el = page.query_selector(f'label[for="{input_id}"]')
            if label_el:
                label_text = label_el.inner_text()

        identifier = f"{label_text} {placeholder} {input_name} {aria_label} {input_id}".lower().strip()
        if not identifier:
            continue

        filled = False
        # Built-in identity autofill — skipped for screener/EEO questions
        # so a long question can't substring-match an identity pattern and
        # leak personal data (e.g. city into a visa question). Those are
        # handled only by the explicit custom rules below.
        if not _is_screener_question(identifier):
            for pattern, key in FIELD_PATTERNS.items():
                if re.search(pattern, identifier):
                    value = AUTOFILL_DATA.get(key, "")
                    if value:
                        try:
                            inp.fill(value)
                            print(f"    ✏️  {key}: {value[:30]}")
                        except Exception:
                            pass
                    filled = True
                    break

        # Try custom field patterns from form_config.json.
        # "a|b|c" values are dropdown candidates — for a text input the
        # first candidate is the answer.
        if not filled:
            for rule in CUSTOM_FIELDS:
                pattern = rule.get("pattern", "")
                value = (rule.get("value", "") or "").split("|")[0].strip()
                if pattern and value and re.search(pattern, identifier):
                    try:
                        inp.fill(value)
                        print(f"    ✏️  custom({pattern}): {value[:30]}")
                    except Exception:
                        pass
                    filled = True
                    break

        # EEO / self-ID fields are rendered as comboboxes (<input>) on
        # Greenhouse, so the <select> pass below never sees them. Best-effort
        # match them here against the same select rules, trying each
        # candidate answer as typed text.
        if not filled:
            for rule in SELECT_DEFAULTS:
                pattern = rule.get("pattern", "")
                raw_value = rule.get("value", "")
                if pattern and raw_value and re.search(pattern, identifier):
                    for candidate in [v.strip() for v in raw_value.split("|") if v.strip()]:
                        try:
                            inp.fill(candidate)
                            print(f"    ✏️  eeo({pattern}): {candidate}")
                            break
                        except Exception:
                            continue
                    break

    # Handle select/dropdown fields with defaults
    selects = page.query_selector_all("select:visible")
    for sel in selects:
        sel_id = sel.get_attribute("id") or ""
        sel_name = sel.get_attribute("name") or ""
        aria_label = sel.get_attribute("aria-label") or ""
        label_text = ""
        if sel_id:
            label_el = page.query_selector(f'label[for="{sel_id}"]')
            if label_el:
                label_text = label_el.inner_text()
        identifier = f"{label_text} {sel_name} {aria_label} {sel_id}".lower().strip()

        for rule in SELECT_DEFAULTS:
            pattern = rule.get("pattern", "")
            raw_value = rule.get("value", "")
            if pattern and raw_value and re.search(pattern, identifier):
                # "a|b|c" = candidate answers tried in order — dropdown
                # option wording differs per ATS ("Decline To Self
                # Identify" on Greenhouse vs "Prefer not to say" on Lever)
                for candidate in [v.strip() for v in raw_value.split("|") if v.strip()]:
                    try:
                        sel.select_option(label=candidate)
                        print(f"    ✏️  select({pattern}): {candidate}")
                        break
                    except Exception:
                        try:
                            sel.select_option(value=candidate)
                            print(f"    ✏️  select({pattern}): {candidate}")
                            break
                        except Exception:
                            continue
                break


def upload_resume(page: Page, pdf_path: str) -> bool:
    file_inputs = page.query_selector_all('input[type="file"]')
    if not file_inputs or not pdf_path or not Path(pdf_path).exists():
        return False
    file_inputs[0].set_input_files(pdf_path)
    print(f"    📎 Uploaded: {Path(pdf_path).name}")
    time.sleep(2)
    return True


def handle_easy_apply(page: Page, pdf_path: str, dry_run: bool = False) -> bool:
    btn = page.query_selector(
        'button.jobs-apply-button, button[aria-label*="Easy Apply"], '
        'button[aria-label*="easy apply"], .indeed-apply-button'
    )
    if not btn:
        print("    ⚠️  Easy Apply button not found")
        return False

    confirm = input("\n    ⚡ Easy Apply found. Enter to proceed, 's' to skip: ").strip()
    if confirm.lower() == "s":
        return False

    btn.click()
    time.sleep(2)

    for _ in range(6):
        fill_form_fields(page)
        upload_resume(page, pdf_path)
        time.sleep(1)

        next_btn = page.query_selector(
            'button[aria-label*="Continue"], button[aria-label*="Next"], '
            'button[aria-label*="Review"], button[aria-label*="Submit"]'
        )
        if not next_btn:
            break

        label = (next_btn.get_attribute("aria-label") or next_btn.inner_text()).lower()
        if "submit" in label:
            if dry_run:
                print("    🏁 DRY RUN — would submit here. Skipping.")
                return False
            confirm = input("\n    🚀 SUBMIT? Enter to send, 's' to skip: ").strip()
            if confirm.lower() == "s":
                return False
            next_btn.click()
            print("    ✅ Submitted!")
            return True
        else:
            next_btn.click()
            time.sleep(1)

    return False


def handle_form_apply(page: Page, pdf_path: str, dry_run: bool = False) -> bool:
    fill_form_fields(page)
    uploaded = upload_resume(page, pdf_path)

    print(f"\n    📋 Form filled. Resume {'uploaded' if uploaded else 'not uploaded'}.")
    if dry_run:
        print("    🏁 DRY RUN — review the browser, nothing will be submitted.")
        input("    Press Enter to continue to next job: ")
        return False

    confirm = input("    Review in browser. Enter when done, 's' to skip: ").strip()
    return confirm.lower() != "s"


# ── Main Apply Flow ───────────────────────────────────────

def apply_to_job(page: Page, job: dict, dry_run: bool = False) -> dict:
    url = job.get("url", "")
    if not url:
        return {"success": False, "reason": "No URL"}

    title = job.get("title", "Unknown")
    company = job.get("company", "Unknown")
    resume_file = job.get("recommended_resume", "")

    print(f"\n{'─'*60}")
    print(f"  📋 {title} @ {company}")
    print(f"  🔗 {url}")
    print(f"  📄 Resume: {resume_file or 'fallback'}")

    pdf_path = get_resume_by_filename(resume_file)
    if pdf_path:
        print(f"    Using: {Path(pdf_path).name}")
    else:
        print(f"    ⚠️  No resume found")

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)
    except Exception as e:
        return {"success": False, "reason": f"Page load failed: {e}"}

    detected = detect_apply_type(page)
    print(f"  🔍 Detected: {detected}")

    success = False
    if detected == "easy-apply":
        success = handle_easy_apply(page, pdf_path, dry_run)
    elif detected in ("resume-upload", "form-fill"):
        success = handle_form_apply(page, pdf_path, dry_run)
    else:
        print(f"  ✍️  Manual — apply in the browser window.")
        input("  Press Enter when done: ")

    return {
        "success": success,
        "resume_used": Path(pdf_path).name if pdf_path else "",
    }


def run_apply_session(dry_run: bool = False):
    ws = get_worksheet()
    ready_jobs = pull_ready_jobs(ws)

    if not ready_jobs:
        print("\n  No jobs marked 'Y' in the Apply column.")
        print("  Put Y in the Apply column for jobs you want, save the CSV, then re-run.")
        return

    print(f"\n{'='*60}")
    print(f"  🚀 Apply Session: {len(ready_jobs)} jobs")
    print(f"  Mode: {'DRY RUN' if dry_run else 'LIVE (will pause before submit)'}")
    print(f"{'='*60}")

    applied = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        for i, job in enumerate(ready_jobs):
            print(f"\n[{i+1}/{len(ready_jobs)}]", end="")
            try:
                result = apply_to_job(page, job, dry_run)
                if result["success"]:
                    row_ref = job.get("sheet_row") or job.get("csv_row_index")
                    mark_applied(ws, row_ref, result.get("resume_used", ""))
                    applied.append(job)
            except Exception as e:
                print(f"  ❌ Error: {e}")
            time.sleep(2)

        browser.close()

    print(f"\n{'='*60}")
    print(f"  ✅ Applied: {len(applied)}")
    print(f"  ⏭️  Skipped: {len(ready_jobs) - len(applied)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="Profile to use")
    parser.add_argument("--dry-run", action="store_true", help="Open browser but don't submit")
    args = parser.parse_args()
    run_apply_session(dry_run=args.dry_run)
