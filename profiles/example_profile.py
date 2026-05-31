"""
PROFILE TEMPLATE — Copy and rename for each person:
    cp profiles/example_profile.py profiles/jane.py

Fill in USER_PROFILE, then add as many roles as you need to ROLE_PROFILES.
Each role gets its own resume PDF and search queries.

    python run_scrape.py --profile jane
"""

GOOGLE_SHEET_ID = "PASTE_SHEET_ID_HERE"  # Only needed if STORAGE_MODE = "google"
GOOGLE_SHEET_NAME = "Job Tracker"

# "local" = CSV file (no setup, open in Excel/Numbers/LibreOffice)
# "google" = Google Sheets (requires service account — see CLAUDE.md)
STORAGE_MODE = "local"

USER_PROFILE = {
    "name": "First Last",
    "email": "email@example.com",
    "phone": "(555) 123-4567",
    "key_skills": ["Skill 1", "Skill 2"],
    "experience_years": 0,
    "current_role": "Title @ Company",
    "linkedin": "",
    "city": "City",
    "state": "ST",
    "country": "United States",
    "portfolio_urls": [],
}

# ── Role Profiles ─────────────────────────────────────────────
# Add as many roles as you want. Each role = search queries + salary range
# + resume PDF filename. Drop PDFs in output/{profile}/resumes/
#
# The key (e.g., "role-1") is a short slug used internally.
# More roles = broader job search, but each role adds API calls per scrape.

ROLE_PROFILES = {
    "role-1": {
        "label": "Role Category Name",
        "salary_min": 70000,
        "salary_max": 120000,
        "resume_file": "FirstLast_Role1.pdf",
        "search_queries": ["Job Title 1", "Job Title 2"],
    },
    # Add more roles as needed:
    # "role-2": {
    #     "label": "Another Category",
    #     "salary_min": 80000,
    #     "salary_max": 130000,
    #     "resume_file": "FirstLast_Role2.pdf",
    #     "search_queries": ["Job Title A", "Job Title B"],
    # },
}

INTERESTING_ROLE = {
    "salary_min": 70000,
    "salary_max": 140000,
    "resume_file": "FirstLast_Role1.pdf",
}

SEARCH_SETTINGS = {
    "locations": ["Remote", "City, ST"],
    "experience_max": 7,
    "exclude_keywords": ["Senior Director", "VP ", "10+ years", "PhD required"],
    "max_results_per_query": 25,

    # ── Stale job cleanup ──
    # Remove unapproved jobs older than this many days when a new scrape runs.
    # Jobs marked Y or Done are never removed. Set to 0 to disable.
    "stale_days": 30,

    # ── Web search (broader internet, not just job boards) ──
    # Searches Google/DuckDuckGo for job postings + checks extra company career pages.
    # Enable here or use --web flag on run_scrape.py
    "web_search": True,
}

# Location filter — controls which jobs make it into the CSV.
# Only Remote jobs + jobs in nearby_cities are kept. Everything else is dropped.
# To relocate: change city, state, and update the nearby_cities list.
LOCATION_FILTER = {
    "city": "City",
    "state": "ST",
    "radius_miles": 20,
    "nearby_cities": [
        # Add cities/towns within your desired radius here
    ],
    "include_remote": True,
}
