"""
Admin Panel API Server
Lightweight Flask server that connects directly to the job-hunter project files.
Runs on localhost:5175 — no external hosting needed.

Multi-user support:
    - Local mode (default): single user, profile dropdown
    - Deployed mode: expandable per-user sections, profile creation, resume upload
    Set DEPLOYED=1 env var or pass --deployed flag for deployed mode.

Usage:
    python admin/server.py              # local mode
    python admin/server.py --deployed   # deployed mode
"""
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

# Add parent dir to path so we can import project modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, jsonify, request, send_from_directory, send_file

app = Flask(__name__, static_folder="static")

# Deployed mode = multi-user with expandable sections + profile creation
DEPLOYED_MODE = os.environ.get("DEPLOYED", "0") == "1" or "--deployed" in sys.argv

# ── Helpers ──────────────────────────────────────────────

PROFILES_DIR = PROJECT_ROOT / "profiles"
OUTPUT_DIR = PROJECT_ROOT / "output"

SHEET_COLUMNS = [
    "Job Title", "Company", "Location", "Work Type", "Salary",
    "Role Category", "Match Reason", "Apply Method", "Apply",
    "Resume Version", "URL", "Source", "Date Posted", "Date Found",
    "Date Applied", "Notes",
]

BROWSER_COLUMNS = [
    "Job Title", "Company", "Location", "Work Type", "Salary",
    "Role Category", "Source", "Easy Apply", "Direct Apply Link",
    "Apply", "URL", "Date Found", "Notes",
]


def _list_profiles():
    """List available profile names."""
    profiles = []
    for f in PROFILES_DIR.glob("*.py"):
        if f.stem not in ("__init__", "example_profile"):
            profiles.append(f.stem)
    return sorted(profiles)


def _profile_dir(name):
    return OUTPUT_DIR / name


def _read_csv(filepath, columns=None):
    """Read CSV file and return list of dicts."""
    if not filepath.exists():
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def _write_csv(filepath, rows, columns):
    """Write list of dicts to CSV."""
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _load_profile_module(name):
    """Parse profile Python file and extract config dicts."""
    profile_file = PROFILES_DIR / f"{name}.py"
    if not profile_file.exists():
        return None

    # Use exec to load the profile
    namespace = {}
    with open(profile_file) as f:
        exec(f.read(), namespace)

    return {
        "name": name,
        "user_profile": namespace.get("USER_PROFILE", {}),
        "role_profiles": namespace.get("ROLE_PROFILES", []),
        "search_settings": namespace.get("SEARCH_SETTINGS", {}),
        "location_filter": namespace.get("LOCATION_FILTER", {}),
        "interesting_role": namespace.get("INTERESTING_ROLE", {}),
    }


def _run_log_path(profile):
    return _profile_dir(profile) / "run_log.json"


def _read_run_log(profile):
    path = _run_log_path(profile)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return []


def _append_run_log(profile, entry):
    log = _read_run_log(profile)
    log.append(entry)
    path = _run_log_path(profile)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(log, f, indent=2)


# ── Static files (UI) ───────────────────────────────────

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)


# ── Profile endpoints ───────────────────────────────────

@app.route("/api/profiles")
def list_profiles():
    profiles = _list_profiles()
    result = []
    for p in profiles:
        pdir = _profile_dir(p)
        jobs_file = pdir / "jobs.csv"
        browser_file = pdir / "browser_jobs.csv"
        job_count = len(_read_csv(jobs_file)) if jobs_file.exists() else 0
        browser_count = len(_read_csv(browser_file)) if browser_file.exists() else 0
        resumes = list((pdir / "resumes").glob("*.pdf")) if (pdir / "resumes").exists() else []
        result.append({
            "name": p,
            "job_count": job_count,
            "browser_job_count": browser_count,
            "resume_count": len(resumes),
        })
    return jsonify(result)


@app.route("/api/profiles/<name>")
def get_profile(name):
    data = _load_profile_module(name)
    if not data:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(data)


@app.route("/api/profiles/<name>/location")
def get_location_filter(name):
    data = _load_profile_module(name)
    if not data:
        return jsonify({"error": "Profile not found"}), 404
    return jsonify(data.get("location_filter", {}))


@app.route("/api/profiles/<name>/search-settings", methods=["PATCH"])
def update_search_settings(name):
    """Update specific search settings in the profile .py file."""
    profile_file = PROFILES_DIR / f"{name}.py"
    if not profile_file.exists():
        return jsonify({"error": "Profile not found"}), 404

    updates = request.json or {}
    content = profile_file.read_text()

    for key, value in updates.items():
        if key == "web_search":
            # Toggle web_search: True/False
            val_str = "True" if value else "False"
            # Try to replace existing key
            new_content = re.sub(
                r'("web_search"\s*:\s*)(True|False)',
                rf'\g<1>{val_str}',
                content,
            )
            if new_content == content:
                # Key doesn't exist — insert before closing brace of SEARCH_SETTINGS
                new_content = content.replace(
                    '"max_results_per_query"',
                    f'"max_results_per_query"',
                )
                # Find the last line before SEARCH_SETTINGS closing }
                new_content = re.sub(
                    r'(SEARCH_SETTINGS\s*=\s*\{[^}]*)',
                    rf'\g<1>\n    "web_search": {val_str},',
                    content, count=1,
                )
            content = new_content

        elif key == "stale_days":
            val_int = int(value) if value else 0
            new_content = re.sub(
                r'("stale_days"\s*:\s*)\d+',
                rf'\g<1>{val_int}',
                content,
            )
            if new_content == content:
                new_content = re.sub(
                    r'(SEARCH_SETTINGS\s*=\s*\{[^}]*)',
                    rf'\g<1>\n    "stale_days": {val_int},',
                    content, count=1,
                )
            content = new_content

    profile_file.write_text(content)
    return jsonify({"ok": True})


# ── Job endpoints ────────────────────────────────────────

@app.route("/api/jobs/<profile>")
def get_jobs(profile):
    source = request.args.get("source", "api")
    if source == "browser":
        filepath = _profile_dir(profile) / "browser_jobs.csv"
        columns = BROWSER_COLUMNS
    else:
        filepath = _profile_dir(profile) / "jobs.csv"
        columns = SHEET_COLUMNS

    rows = _read_csv(filepath)

    # Add index to each row
    for i, row in enumerate(rows):
        row["_index"] = i

    # Apply filters
    work_type = request.args.get("work_type")
    if work_type:
        types = work_type.split(",")
        rows = [r for r in rows if r.get("Work Type", "") in types]

    category = request.args.get("category")
    if category:
        rows = [r for r in rows if category.lower() in r.get("Role Category", "").lower()]

    apply_filter = request.args.get("apply")
    if apply_filter:
        rows = [r for r in rows if (r.get("Apply", "") or "").strip().upper() == apply_filter.upper()]

    search = request.args.get("search")
    if search:
        s = search.lower()
        rows = [r for r in rows if s in r.get("Job Title", "").lower()
                or s in r.get("Company", "").lower()
                or s in r.get("Location", "").lower()]

    return jsonify({
        "jobs": rows,
        "total": len(rows),
        "columns": columns,
    })


@app.route("/api/jobs/<profile>/<int:index>", methods=["PATCH"])
def update_job(profile, index):
    source = request.args.get("source", "api")
    if source == "browser":
        filepath = _profile_dir(profile) / "browser_jobs.csv"
        columns = BROWSER_COLUMNS
    else:
        filepath = _profile_dir(profile) / "jobs.csv"
        columns = SHEET_COLUMNS

    rows = _read_csv(filepath)
    if index < 0 or index >= len(rows):
        return jsonify({"error": "Invalid index"}), 400

    updates = request.json
    for key, value in updates.items():
        if key in columns:
            rows[index][key] = value

    _write_csv(filepath, rows, columns)
    return jsonify({"ok": True, "row": rows[index]})


@app.route("/api/jobs/<profile>/bulk", methods=["PATCH"])
def bulk_update_jobs(profile):
    source = request.args.get("source", "api")
    if source == "browser":
        filepath = _profile_dir(profile) / "browser_jobs.csv"
        columns = BROWSER_COLUMNS
    else:
        filepath = _profile_dir(profile) / "jobs.csv"
        columns = SHEET_COLUMNS

    rows = _read_csv(filepath)
    body = request.json
    indices = body.get("indices", [])
    updates = body.get("updates", {})

    count = 0
    for idx in indices:
        if 0 <= idx < len(rows):
            for key, value in updates.items():
                if key in columns:
                    rows[idx][key] = value
            count += 1

    _write_csv(filepath, rows, columns)
    return jsonify({"ok": True, "updated": count})


@app.route("/api/jobs/<profile>/stats")
def job_stats(profile):
    api_rows = _read_csv(_profile_dir(profile) / "jobs.csv")
    browser_rows = _read_csv(_profile_dir(profile) / "browser_jobs.csv")

    def _stats(rows):
        total = len(rows)
        approved = sum(1 for r in rows if (r.get("Apply", "") or "").strip().upper() == "Y")
        applied = sum(1 for r in rows if (r.get("Apply", "") or "").strip().upper() == "DONE")
        remote = sum(1 for r in rows if r.get("Work Type", "") == "Remote")
        categories = {}
        sources = {}
        for r in rows:
            cat = r.get("Role Category", "Unmatched") or "Unmatched"
            categories[cat] = categories.get(cat, 0) + 1
            src = r.get("Source", "Unknown") or "Unknown"
            sources[src] = sources.get(src, 0) + 1
        return {
            "total": total, "approved": approved, "applied": applied,
            "remote": remote, "categories": categories, "sources": sources,
        }

    return jsonify({
        "api": _stats(api_rows),
        "browser": _stats(browser_rows),
    })


# ── Scrape/Apply endpoints ──────────────────────────────

# Track running processes
_running = {}


@app.route("/api/scrape/<profile>", methods=["POST"])
def run_scrape(profile):
    scrape_type = request.json.get("type", "api")  # "api", "browser", "both"

    if profile in _running:
        return jsonify({"error": "Already running", "status": "running"}), 409

    def _run(cmd, key):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=600,
                cwd=str(PROJECT_ROOT),
                env={**os.environ, "PYTHONUNBUFFERED": "1"},
            )
            _append_run_log(profile, {
                "type": scrape_type,
                "date": datetime.now().isoformat(),
                "status": "complete" if result.returncode == 0 else "error",
                "stdout": result.stdout[-2000:] if result.stdout else "",
                "stderr": result.stderr[-1000:] if result.stderr else "",
                "duration_hint": "check log",
            })
        except subprocess.TimeoutExpired:
            _append_run_log(profile, {
                "type": scrape_type,
                "date": datetime.now().isoformat(),
                "status": "timeout",
            })
        finally:
            _running.pop(key, None)

    venv_python = str(PROJECT_ROOT / "venv" / "bin" / "python")

    if scrape_type in ("api", "both"):
        key = f"{profile}_api"
        cmd = [venv_python, "run_scrape.py", "--profile", profile]
        # Check if web search is enabled for this profile
        profile_data = _load_profile_module(profile)
        if profile_data:
            ss = profile_data.get("search_settings", {})
            if ss.get("web_search", False):
                cmd.append("--web")
            if not ss.get("stale_days", 30):
                cmd.append("--no-cleanup")
            # Include browser scrape in the API run if "both" or profile enables it
            if scrape_type == "both" or ss.get("browser_scrape", False):
                cmd.append("--browsers")
        _running[key] = True
        threading.Thread(target=_run, args=(cmd, key), daemon=True).start()

    if scrape_type in ("browser",):
        key = f"{profile}_browser"
        cmd = [venv_python, "run_scrape_browsers.py", "--profile", profile]
        _running[key] = True
        threading.Thread(target=_run, args=(cmd, key), daemon=True).start()

    return jsonify({"ok": True, "status": "started", "type": scrape_type})


@app.route("/api/scrape/status")
def scrape_status():
    return jsonify({"running": list(_running.keys())})


# ── Form Config endpoints ───────────────────────────────

@app.route("/api/form-config/<profile>")
def get_form_config(profile):
    config_path = _profile_dir(profile) / "form_config.json"
    if config_path.exists():
        with open(config_path) as f:
            return jsonify(json.load(f))

    example = PROJECT_ROOT / "form_config_example.json"
    if example.exists():
        with open(example) as f:
            return jsonify(json.load(f))

    return jsonify({"custom_fields": [], "select_defaults": []})


@app.route("/api/form-config/<profile>", methods=["PUT"])
def update_form_config(profile):
    config_path = _profile_dir(profile) / "form_config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(request.json, f, indent=2)
    return jsonify({"ok": True})


# ── Resume endpoints ────────────────────────────────────

@app.route("/api/resumes/<profile>")
def list_resumes(profile):
    resume_dir = _profile_dir(profile) / "resumes"
    if not resume_dir.exists():
        return jsonify([])

    resumes = []
    for f in sorted(resume_dir.glob("*.pdf")):
        resumes.append({
            "filename": f.name,
            "size_kb": round(f.stat().st_size / 1024, 1),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
        })
    return jsonify(resumes)


@app.route("/api/resumes/<profile>/<filename>")
def serve_resume(profile, filename):
    resume_path = _profile_dir(profile) / "resumes" / filename
    if not resume_path.exists():
        return jsonify({"error": "Not found"}), 404
    return send_file(resume_path, mimetype="application/pdf")


# ── Run History endpoints ───────────────────────────────

@app.route("/api/history/<profile>")
def get_history(profile):
    log = _read_run_log(profile)
    return jsonify(log[-50:])  # Last 50 runs


# ── Setup check endpoint ────────────────────────────────

@app.route("/api/setup")
def setup_check():
    checks = {}

    # Python version
    checks["python"] = {
        "ok": sys.version_info >= (3, 10),
        "detail": f"Python {sys.version_info.major}.{sys.version_info.minor}",
    }

    # Venv
    venv_path = PROJECT_ROOT / "venv"
    checks["venv"] = {
        "ok": venv_path.exists(),
        "detail": str(venv_path) if venv_path.exists() else "Not found",
    }

    # Dependencies
    reqs = PROJECT_ROOT / "requirements.txt"
    checks["deps"] = {
        "ok": reqs.exists(),
        "detail": "requirements.txt exists" if reqs.exists() else "Missing",
    }

    # Profiles
    profiles = _list_profiles()
    checks["profiles"] = {
        "ok": len(profiles) > 0,
        "detail": ", ".join(profiles) if profiles else "No profiles",
    }

    # Env file
    env_file = PROJECT_ROOT / ".env"
    checks["env"] = {
        "ok": True,  # Not required for local
        "detail": "Found" if env_file.exists() else "Not found (optional)",
    }

    # Per-profile checks
    profile_checks = {}
    for p in profiles:
        pdir = _profile_dir(p)
        resume_dir = pdir / "resumes"
        resumes = list(resume_dir.glob("*.pdf")) if resume_dir.exists() else []
        jobs = pdir / "jobs.csv"
        form_cfg = pdir / "form_config.json"
        profile_checks[p] = {
            "has_resumes": len(resumes) > 0,
            "resume_count": len(resumes),
            "has_jobs": jobs.exists() and jobs.stat().st_size > 100,
            "has_form_config": form_cfg.exists(),
        }

    checks["profile_details"] = profile_checks

    return jsonify(checks)


# ── Mode endpoint ──────────────────────────────────────

@app.route("/api/mode")
def get_mode():
    return jsonify({"deployed": DEPLOYED_MODE})


# ── Profile creation (deployed mode) ──────────────────

@app.route("/api/profiles", methods=["POST"])
def create_profile():
    body = request.json or {}
    name = (body.get("name") or "").strip().lower()
    name = re.sub(r"[^a-z0-9_]", "", name)

    if not name or len(name) < 2:
        return jsonify({"error": "Name must be 2+ lowercase letters/numbers"}), 400

    profile_file = PROFILES_DIR / f"{name}.py"
    if profile_file.exists():
        return jsonify({"error": f"Profile '{name}' already exists"}), 409

    # Build a fresh profile with person info — roles added separately
    user_info = body.get("user_info", {})
    person_name = user_info.get("name", "First Last")
    email = user_info.get("email", "email@example.com")
    phone = user_info.get("phone", "(555) 123-4567")
    city = user_info.get("city", "City")
    state = user_info.get("state", "ST")
    country = user_info.get("country", "United States")
    linkedin = user_info.get("linkedin", "")
    key_skills = user_info.get("key_skills", [])
    experience_years = user_info.get("experience_years", 0)
    current_role = user_info.get("current_role", "")

    content = f'''"""
Profile: {person_name}
Run with: python run_scrape.py --profile {name}
"""

GOOGLE_SHEET_ID = ""
GOOGLE_SHEET_NAME = "Job Tracker"
STORAGE_MODE = "local"

USER_PROFILE = {{
    "name": {repr(person_name)},
    "email": {repr(email)},
    "phone": {repr(phone)},
    "key_skills": {repr(key_skills)},
    "experience_years": {experience_years},
    "current_role": {repr(current_role)},
    "linkedin": {repr(linkedin)},
    "city": {repr(city)},
    "state": {repr(state)},
    "country": {repr(country)},
    "portfolio_urls": [],
}}

ROLE_PROFILES = {{}}

INTERESTING_ROLE = {{
    "salary_min": 70000,
    "salary_max": 140000,
    "resume_file": "",
}}

SEARCH_SETTINGS = {{
    "locations": ["Remote", "{city}, {state}"],
    "experience_max": 7,
    "exclude_keywords": ["Senior Director", "VP ", "10+ years", "PhD required"],
    "max_results_per_query": 25,
    "stale_days": 30,
    "web_search": True,
}}

LOCATION_FILTER = {{
    "city": {repr(city)},
    "state": {repr(state)},
    "radius_miles": 20,
    "nearby_cities": [],
    "include_remote": True,
}}
'''

    with open(profile_file, "w") as f:
        f.write(content)

    # Create output directories
    out = OUTPUT_DIR / name
    (out / "resumes").mkdir(parents=True, exist_ok=True)
    (out / "data").mkdir(parents=True, exist_ok=True)

    # Copy form config example
    example_cfg = PROJECT_ROOT / "form_config_example.json"
    if example_cfg.exists():
        shutil.copy(example_cfg, out / "form_config.json")

    return jsonify({"ok": True, "name": name})


@app.route("/api/profiles/<name>", methods=["DELETE"])
def delete_profile(name):
    profile_file = PROFILES_DIR / f"{name}.py"
    if not profile_file.exists():
        return jsonify({"error": "Profile not found"}), 404

    # Only delete profile file, keep output data for safety
    profile_file.unlink()
    return jsonify({"ok": True, "name": name, "note": "Output data preserved"})


# ── Role management ──────────────────────────────────

@app.route("/api/profiles/<name>/roles")
def list_roles(name):
    profile_data = _load_profile_module(name)
    if not profile_data:
        return jsonify({"error": "Profile not found"}), 404
    roles = profile_data.get("role_profiles", {})
    if isinstance(roles, dict):
        return jsonify({"roles": roles})
    return jsonify({"roles": {}})


@app.route("/api/profiles/<name>/roles", methods=["POST"])
def add_role(name):
    profile_file = PROFILES_DIR / f"{name}.py"
    if not profile_file.exists():
        return jsonify({"error": "Profile not found"}), 404

    body = request.json or {}
    role_id = (body.get("role_id") or "").strip().lower()
    role_id = re.sub(r"[^a-z0-9_\-]", "", role_id)
    if not role_id or len(role_id) < 2:
        return jsonify({"error": "role_id must be 2+ lowercase letters/numbers/dashes"}), 400

    label = body.get("label", role_id)
    salary_min = int(body.get("salary_min", 0))
    salary_max = int(body.get("salary_max", 0))
    resume_file = body.get("resume_file", "")
    search_queries = body.get("search_queries", [])

    if not search_queries:
        return jsonify({"error": "At least one search query required"}), 400

    profile_data = _load_profile_module(name)
    roles = profile_data.get("role_profiles", {})
    if not isinstance(roles, dict):
        roles = {}

    roles[role_id] = {
        "label": label,
        "salary_min": salary_min,
        "salary_max": salary_max,
        "resume_file": resume_file,
        "search_queries": search_queries,
    }

    _write_role_profiles(name, roles)
    return jsonify({"ok": True, "role_id": role_id, "total_roles": len(roles)})


@app.route("/api/profiles/<name>/roles/<role_id>", methods=["PUT"])
def update_role(name, role_id):
    profile_file = PROFILES_DIR / f"{name}.py"
    if not profile_file.exists():
        return jsonify({"error": "Profile not found"}), 404

    profile_data = _load_profile_module(name)
    roles = profile_data.get("role_profiles", {})
    if role_id not in roles:
        return jsonify({"error": f"Role '{role_id}' not found"}), 404

    body = request.json or {}
    if "label" in body:
        roles[role_id]["label"] = body["label"]
    if "salary_min" in body:
        roles[role_id]["salary_min"] = int(body["salary_min"])
    if "salary_max" in body:
        roles[role_id]["salary_max"] = int(body["salary_max"])
    if "resume_file" in body:
        roles[role_id]["resume_file"] = body["resume_file"]
    if "search_queries" in body:
        roles[role_id]["search_queries"] = body["search_queries"]

    _write_role_profiles(name, roles)
    return jsonify({"ok": True, "role_id": role_id})


@app.route("/api/profiles/<name>/roles/<role_id>", methods=["DELETE"])
def delete_role(name, role_id):
    profile_file = PROFILES_DIR / f"{name}.py"
    if not profile_file.exists():
        return jsonify({"error": "Profile not found"}), 404

    profile_data = _load_profile_module(name)
    roles = profile_data.get("role_profiles", {})
    if role_id not in roles:
        return jsonify({"error": f"Role '{role_id}' not found"}), 404

    del roles[role_id]
    _write_role_profiles(name, roles)
    return jsonify({"ok": True, "role_id": role_id, "remaining_roles": len(roles)})


def _write_role_profiles(name, roles):
    """Rewrite the ROLE_PROFILES dict in the profile file.

    Uses line-based replacement to handle arbitrarily nested dicts
    with multi-line values (e.g. search_queries spanning many lines).
    """
    profile_file = PROFILES_DIR / f"{name}.py"
    with open(profile_file) as f:
        src_lines = f.readlines()

    # Build the new ROLE_PROFILES block
    new_lines = ["ROLE_PROFILES = {\n"]
    for rid, role in roles.items():
        new_lines.append(f'    "{rid}": {{\n')
        new_lines.append(f'        "label": {repr(role.get("label", rid))},\n')
        new_lines.append(f'        "salary_min": {role.get("salary_min", 0)},\n')
        new_lines.append(f'        "salary_max": {role.get("salary_max", 0)},\n')
        new_lines.append(f'        "resume_file": {repr(role.get("resume_file", ""))},\n')
        new_lines.append(f'        "search_queries": {repr(role.get("search_queries", []))},\n')
        new_lines.append("    },\n")
    new_lines.append("}\n")

    # Find the start line (ROLE_PROFILES = {) and end line (matching closing brace)
    start_idx = None
    for i, line in enumerate(src_lines):
        if line.lstrip().startswith("ROLE_PROFILES") and "=" in line:
            start_idx = i
            break

    if start_idx is not None:
        # Walk forward from start to find the closing brace at indent level 0.
        # Track brace depth: the opening { on the ROLE_PROFILES line starts at 1.
        depth = 0
        end_idx = start_idx
        for i in range(start_idx, len(src_lines)):
            depth += src_lines[i].count("{") - src_lines[i].count("}")
            if depth <= 0:
                end_idx = i
                break

        # Replace lines [start_idx .. end_idx] with new block
        result = src_lines[:start_idx] + new_lines + src_lines[end_idx + 1:]
    else:
        # No existing block — append
        result = src_lines + ["\n"] + new_lines

    with open(profile_file, "w") as f:
        f.writelines(result)


# ── Resume upload ────────────────────────────────────

@app.route("/api/resumes/<profile>/upload", methods=["POST"])
def upload_resume(profile):
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    f = request.files["file"]
    if not f.filename or not f.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files accepted"}), 400

    resume_dir = _profile_dir(profile) / "resumes"
    resume_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename
    safe_name = re.sub(r"[^a-zA-Z0-9_\-.]", "_", f.filename)
    save_path = resume_dir / safe_name
    f.save(str(save_path))

    return jsonify({
        "ok": True,
        "filename": safe_name,
        "size_kb": round(save_path.stat().st_size / 1024, 1),
    })


@app.route("/api/resumes/<profile>/<filename>", methods=["DELETE"])
def delete_resume(profile, filename):
    resume_path = _profile_dir(profile) / "resumes" / filename
    if not resume_path.exists():
        return jsonify({"error": "Not found"}), 404
    resume_path.unlink()
    return jsonify({"ok": True})


# ── All-users summary (deployed mode) ─────────────────

@app.route("/api/all-users")
def all_users_summary():
    """Return summary for all profiles in one call."""
    profiles = _list_profiles()
    users = []
    for p in profiles:
        pdir = _profile_dir(p)
        jobs_file = pdir / "jobs.csv"
        browser_file = pdir / "browser_jobs.csv"
        api_rows = _read_csv(jobs_file) if jobs_file.exists() else []
        browser_rows = _read_csv(browser_file) if browser_file.exists() else []
        resumes = list((pdir / "resumes").glob("*.pdf")) if (pdir / "resumes").exists() else []

        profile_data = _load_profile_module(p)
        user_name = ""
        user_email = ""
        if profile_data:
            up = profile_data.get("user_profile", {})
            user_name = up.get("name", p)
            user_email = up.get("email", "")

        approved = sum(1 for r in api_rows if (r.get("Apply", "") or "").strip().upper() == "Y")
        applied = sum(1 for r in api_rows if (r.get("Apply", "") or "").strip().upper() == "DONE")
        b_approved = sum(1 for r in browser_rows if (r.get("Apply", "") or "").strip().upper() == "Y")
        b_applied = sum(1 for r in browser_rows if (r.get("Apply", "") or "").strip().upper() == "DONE")

        users.append({
            "profile": p,
            "display_name": user_name,
            "email": user_email,
            "api_jobs": len(api_rows),
            "browser_jobs": len(browser_rows),
            "approved": approved + b_approved,
            "applied": applied + b_applied,
            "resume_count": len(resumes),
            "resume_files": [r.name for r in resumes],
        })

    return jsonify(users)


# ── Main ────────────────────────────────────────────────

if __name__ == "__main__":
    mode = "DEPLOYED" if DEPLOYED_MODE else "LOCAL"
    print(f"\n  Admin Panel starting... ({mode} mode)")
    print(f"  Project root: {PROJECT_ROOT}")
    print(f"  Profiles: {', '.join(_list_profiles())}")
    print(f"\n  Open http://localhost:5175\n")
    app.run(host="127.0.0.1", port=5175, debug=True)
