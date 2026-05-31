"""
Configuration loader.
Loads the active profile by name from profiles/ directory.

Usage:
    python run_scrape.py --profile alex
    ACTIVE_PROFILE=alex python run_scrape.py
"""
import os
import sys
import importlib.util
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CREDS_PATH = os.getenv("GOOGLE_CREDS_PATH", "credentials/google_service_account.json")


def _get_profile_name() -> str:
    for i, arg in enumerate(sys.argv):
        if arg == "--profile" and i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return os.getenv("ACTIVE_PROFILE", "alex")


def _load_profile(name: str):
    profiles_dir = Path(__file__).parent / "profiles"
    profile_file = profiles_dir / f"{name}.py"

    if not profile_file.exists():
        available = [
            f.stem for f in profiles_dir.glob("*.py")
            if f.stem not in ("__init__", "example_profile")
        ]
        print(f"\n❌ Profile '{name}' not found at: {profile_file}")
        if available:
            print(f"   Available profiles: {', '.join(available)}")
        print(f"   Create one: cp profiles/example_profile.py profiles/{name}.py\n")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location(f"profiles.{name}", profile_file)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ACTIVE_PROFILE_NAME = _get_profile_name()
_profile = _load_profile(ACTIVE_PROFILE_NAME)

USER_PROFILE = _profile.USER_PROFILE
ROLE_PROFILES = _profile.ROLE_PROFILES
# Merge profile SEARCH_SETTINGS with defaults for new keys
_DEFAULT_SEARCH_SETTINGS = {
    "stale_days": 21,
    "web_search": False,
}
SEARCH_SETTINGS = {**_DEFAULT_SEARCH_SETTINGS, **_profile.SEARCH_SETTINGS}
INTERESTING_ROLE = getattr(_profile, "INTERESTING_ROLE", {
    "salary_min": 60000, "salary_max": 150000, "resume_file": "",
})
GOOGLE_SHEET_ID = getattr(_profile, "GOOGLE_SHEET_ID", os.getenv("GOOGLE_SHEET_ID", ""))
GOOGLE_SHEET_NAME = getattr(_profile, "GOOGLE_SHEET_NAME", "Job Tracker")
LOCATION_FILTER = getattr(_profile, "LOCATION_FILTER", {
    "city": "Nashua", "state": "NH", "radius_miles": 20,
    "nearby_cities": [], "include_remote": True,
})

# Storage mode: "local" (CSV file) or "google" (Google Sheets)
# Set in your profile or .env. Defaults to "local" (no setup needed).
STORAGE_MODE = getattr(_profile, "STORAGE_MODE", os.getenv("STORAGE_MODE", "local"))

# Per-profile output directories
PROFILE_DIR = Path(f"output/{ACTIVE_PROFILE_NAME}")
DATA_DIR = PROFILE_DIR / "data"
RESUMES_DIR = PROFILE_DIR / "resumes"

for _d in [DATA_DIR, RESUMES_DIR]:
    _d.mkdir(parents=True, exist_ok=True)

SHEET_COLUMNS = [
    "Job Title",
    "Company",
    "Location",
    "Work Type",
    "Salary",
    "Role Category",
    "Match Reason",
    "Apply Method",
    "Apply",
    "Resume Version",
    "URL",
    "Source",
    "Date Posted",
    "Date Found",
    "Date Applied",
    "Notes",
]

print(f"  📋 Profile: {ACTIVE_PROFILE_NAME}")
print(f"  👤 {USER_PROFILE['name']}")
print(f"  💾 Storage: {STORAGE_MODE} {'('+str(PROFILE_DIR/'jobs.csv')+')' if STORAGE_MODE == 'local' else '(Google Sheet)'}")
print(f"  📂 Output: {PROFILE_DIR}/")
