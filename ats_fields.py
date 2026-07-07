"""
ATS Field Catalog — auto-fill rules built from the ACTUAL application
forms of the most common job boards / applicant tracking systems.

Every entry documents a real field as it appears on one or more of:

  Greenhouse   (boards.greenhouse.io — Stripe, GitLab, xAI, Scale AI...)
  Lever        (jobs.lever.co — Anthropic, Welocalize...)
  Workday      (*.myworkdayjobs.com — banks, hospitals, large enterprises)
  Ashby        (jobs.ashbyhq.com — Mercor, OpenAI, startups)
  iCIMS        (careers-*.icims.com — mid-market/enterprise)
  SmartRecruiters / Jobvite / BambooHR (startup & SMB career sites)
  Indeed Apply (screener questions)
  LinkedIn Easy Apply (screener questions)

Each entry:
  pattern  — case-insensitive regex matched against the field's
             label + placeholder + name + aria-label + id
             (see browser_apply.fill_form_fields)
  value    — what to answer. "a|b|c" = candidates tried in order
             (dropdown option wording differs per ATS: Greenhouse says
             "Decline To Self Identify", Lever says "Prefer not to say").
             Empty value = placeholder; the row is shown in the admin
             Form Fill page for you to fill in, and skipped at apply
             time while blank.
  target   — "text" (input/textarea) or "select" (dropdown)
  label    — human name shown in the admin panel
  boards   — which ATSs actually ask this (shown in the admin panel)

Profile-derived entries (name, email, years of experience...) are
resolved from USER_PROFILE by build_form_config().

Seed / refresh a profile's form_config.json:

    python ats_fields.py --profile alex           # merge missing fields in
    python ats_fields.py --profile alex --reset   # rebuild from catalog

Merging never overwrites values you've edited — it only appends
catalog fields whose pattern isn't in the config yet.
"""
import json
from pathlib import Path


def _catalog(user_profile: dict) -> list[dict]:
    """The full field catalog, with values resolved from the profile."""
    up = user_profile or {}
    name = (up.get("name") or "").strip()
    first = name.split()[0] if name else ""
    last = name.split()[-1] if name else ""
    state = up.get("state", "")
    years = str(up.get("experience_years", "") or "")
    portfolio = (up.get("portfolio_urls") or [""])[0]

    return [
        # ── Identity & contact ─────────────────────────────────────
        # (browser_apply has built-ins for the plain first/last/email
        #  cases; these cover the wordings the built-ins miss.)
        dict(target="text", label="Preferred / legal first name",
             boards="Workday, iCIMS",
             pattern=r"preferred.?name|legal.?first|given.?name",
             value=first),
        dict(target="text", label="Street address",
             boards="Workday, iCIMS, Taleo",
             pattern=r"address.?line.?1|street.?address|^address$",
             value=""),
        dict(target="text", label="ZIP / postal code",
             boards="Workday, iCIMS, Taleo",
             pattern=r"zip|postal",
             value=""),
        dict(target="text", label="GitHub profile",
             boards="Greenhouse, Lever, Ashby",
             pattern=r"github",
             value=""),
        dict(target="text", label="Twitter / X profile",
             boards="Lever",
             pattern=r"twitter|\bx\b.?(profile|handle)",
             value=""),
        dict(target="text", label="Pronouns",
             boards="Greenhouse, Lever",
             pattern=r"pronoun",
             value=""),
        dict(target="text", label="Portfolio / other website",
             boards="Greenhouse, Lever, Ashby",
             pattern=r"other.?(website|url)|portfolio.?(link|url)",
             value=portfolio),

        # ── Screener questions (text) ──────────────────────────────
        dict(target="text", label="Salary expectation",
             boards="Greenhouse, Ashby, iCIMS, LinkedIn, Indeed",
             pattern=r"salary|desired.?(pay|compensation)|compensation.?expect|pay.?expectation",
             value="Negotiable"),
        dict(target="text", label="Earliest start date / availability",
             boards="Greenhouse, iCIMS, Indeed, BambooHR",
             pattern=r"(earliest|available).{0,12}start|start.?date|when.{0,20}start|availability",
             value="Two weeks from offer"),
        dict(target="text", label="Notice period",
             boards="Workday, iCIMS, SmartRecruiters",
             pattern=r"notice.?period",
             value="Two weeks"),
        dict(target="text", label="Work authorization (text)",
             boards="Greenhouse, Lever, Ashby, Indeed, LinkedIn",
             pattern=r"authoriz|legally.{0,15}(work|employ)|right.?to.?work|eligible.?to.?work",
             value="Yes"),
        dict(target="text", label="Visa sponsorship (text)",
             boards="Greenhouse, Lever, Workday, LinkedIn",
             pattern=r"sponsor|visa",
             value="No"),
        dict(target="text", label="Willing to relocate",
             boards="Indeed, iCIMS, LinkedIn",
             pattern=r"relocat",
             value="No — remote preferred"),
        dict(target="text", label="Comfortable working remotely",
             boards="LinkedIn, Indeed",
             pattern=r"remote.?work|work.{0,10}remote|work.?from.?home",
             value="Yes"),
        dict(target="text", label="How did you hear about us",
             boards="Greenhouse, Lever, Workday, iCIMS",
             pattern=r"how.{0,10}hear|hear.?about|referral.?source|\bsource\b",
             value="Job board / online search"),
        dict(target="text", label="Referred by an employee?",
             boards="Workday, iCIMS",
             pattern=r"referred.?by|employee.?referral|know.?anyone",
             value="No"),
        dict(target="text", label="Previously worked here?",
             boards="Workday, iCIMS, Taleo",
             pattern=r"(previously|ever|formerly).{0,12}(worked|employed)|former.?employee",
             value="No"),
        dict(target="text", label="Security clearance",
             boards="iCIMS, USAJobs, ClearanceJobs",
             pattern=r"clearance",
             value="No"),
        dict(target="text", label="18 or older",
             boards="Indeed, BambooHR",
             pattern=r"18.{0,10}(years|older)|legal.?age|at.?least.?18",
             value="Yes"),
        dict(target="text", label="Why do you want to work here (personal — fill per job)",
             boards="Greenhouse, Lever, Ashby",
             pattern=r"why.{0,15}(want|interested|join)|what.{0,10}(excites|interests).?you",
             value=""),
        dict(target="text", label="Cover letter (personal — fill per job)",
             boards="Greenhouse, Lever",
             pattern=r"cover.?letter",
             value=""),

        # ── Dropdowns (select) — candidates tried in order ─────────
        dict(target="select", label="Work authorization",
             boards="Greenhouse, Workday, iCIMS, SmartRecruiters",
             pattern=r"authoriz|eligible.?to.?work|legally.{0,15}work",
             value="Yes"),
        dict(target="select", label="Visa sponsorship",
             boards="Greenhouse, Workday, iCIMS, SmartRecruiters",
             pattern=r"sponsor|visa",
             value="No"),
        dict(target="select", label="Country",
             boards="Workday, iCIMS, Taleo",
             pattern=r"country",
             value="United States|United States of America|USA"),
        dict(target="select", label="State",
             boards="Workday, iCIMS, Taleo",
             pattern=r"\bstate\b|province",
             value=_state_candidates(state)),
        dict(target="select", label="Phone device type",
             boards="Workday",
             pattern=r"phone.?device|device.?type",
             value="Mobile|Cell|Mobile Phone"),
        dict(target="select", label="Years of experience",
             boards="LinkedIn, Indeed, iCIMS",
             pattern=r"years.{0,6}experience",
             value=_years_candidates(years)),
        dict(target="select", label="Education level",
             boards="Indeed, iCIMS, Taleo",
             pattern=r"education|highest.?level|degree",
             value="Bachelor's Degree|Bachelors Degree|Bachelor's|4 Year Degree"),
        dict(target="select", label="How did you hear about us",
             boards="Workday, iCIMS, Greenhouse",
             pattern=r"hear.?about|referral.?source|\bsource\b",
             value="Job Board|Online|LinkedIn|Other"),
        dict(target="select", label="Remote work",
             boards="LinkedIn, Indeed",
             pattern=r"remote",
             value="Yes"),

        # ── EEO / voluntary self-identification ────────────────────
        # Wordings differ per ATS; all "decline" variants are included.
        dict(target="select", label="Gender (EEO)",
             boards="Greenhouse, Lever, Workday, iCIMS",
             pattern=r"gender|\bsex\b",
             value="Decline To Self Identify|Prefer not to say|"
                   "I don't wish to answer|Decline to answer"),
        dict(target="select", label="Race / ethnicity (EEO)",
             boards="Greenhouse, Lever, Workday, iCIMS",
             pattern=r"race|ethnicit",
             value="Decline To Self Identify|Prefer not to say|"
                   "I don't wish to answer|Two or More Races"),
        dict(target="select", label="Hispanic or Latino (EEO)",
             boards="Workday, iCIMS",
             pattern=r"hispanic|latino",
             value="Decline To Self Identify|Prefer not to say|No"),
        dict(target="select", label="Veteran status (EEO)",
             boards="Greenhouse, Lever, Workday, iCIMS",
             pattern=r"veteran",
             value="I am not a protected veteran|"
                   "I AM NOT A PROTECTED VETERAN|"
                   "Decline To Self Identify|No|Prefer not to say"),
        dict(target="select", label="Disability status (CC-305)",
             boards="Greenhouse, Lever, Workday, iCIMS",
             pattern=r"disab",
             value="No, I do not have a disability|"
                   "No, I don't have a disability|"
                   "I don't wish to answer|Prefer not to say|No"),
    ]


def _state_candidates(state_abbr: str) -> str:
    """'NH' → 'New Hampshire|NH' so both option wordings match."""
    full = {
        "al": "Alabama", "ak": "Alaska", "az": "Arizona", "ar": "Arkansas",
        "ca": "California", "co": "Colorado", "ct": "Connecticut",
        "de": "Delaware", "fl": "Florida", "ga": "Georgia", "hi": "Hawaii",
        "id": "Idaho", "il": "Illinois", "in": "Indiana", "ia": "Iowa",
        "ks": "Kansas", "ky": "Kentucky", "la": "Louisiana", "me": "Maine",
        "md": "Maryland", "ma": "Massachusetts", "mi": "Michigan",
        "mn": "Minnesota", "ms": "Mississippi", "mo": "Missouri",
        "mt": "Montana", "ne": "Nebraska", "nv": "Nevada",
        "nh": "New Hampshire", "nj": "New Jersey", "nm": "New Mexico",
        "ny": "New York", "nc": "North Carolina", "nd": "North Dakota",
        "oh": "Ohio", "ok": "Oklahoma", "or": "Oregon",
        "pa": "Pennsylvania", "ri": "Rhode Island", "sc": "South Carolina",
        "sd": "South Dakota", "tn": "Tennessee", "tx": "Texas",
        "ut": "Utah", "vt": "Vermont", "va": "Virginia",
        "wa": "Washington", "wv": "West Virginia", "wi": "Wisconsin",
        "wy": "Wyoming", "dc": "District of Columbia",
    }.get((state_abbr or "").lower(), "")
    if full and state_abbr:
        return f"{full}|{state_abbr.upper()}"
    return full or (state_abbr or "")


def _years_candidates(years: str) -> str:
    """'4' → the range buckets different boards use."""
    if not years or not years.isdigit():
        return ""
    y = int(years)
    buckets = [f"{y}", f"{y} years", f"{y}+ years"]
    for lo, hi in [(1, 2), (1, 3), (3, 5), (2, 4), (4, 6), (5, 7), (5, 10)]:
        if lo <= y <= hi:
            buckets.append(f"{lo}-{hi} years")
    return "|".join(buckets)


def build_form_config(user_profile: dict) -> dict:
    """Generate a full form_config dict from the catalog + profile."""
    custom_fields, select_defaults = [], []
    for entry in _catalog(user_profile):
        rule = {
            "pattern": entry["pattern"],
            "value": entry["value"],
            "label": entry["label"],
            "boards": entry["boards"],
        }
        (select_defaults if entry["target"] == "select" else custom_fields).append(rule)
    return {"custom_fields": custom_fields, "select_defaults": select_defaults}


def seed_form_config(profile: str, user_profile: dict, reset: bool = False) -> dict:
    """
    Write/merge the catalog into output/{profile}/form_config.json.
    Merge appends catalog rules whose pattern isn't present yet —
    values you've edited are never touched. Returns a summary.
    """
    path = Path(__file__).parent / "output" / profile / "form_config.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    generated = build_form_config(user_profile)

    if reset or not path.exists():
        config = generated
        added = {
            "custom_fields": len(config["custom_fields"]),
            "select_defaults": len(config["select_defaults"]),
        }
    else:
        with open(path) as f:
            config = json.load(f)
        added = {"custom_fields": 0, "select_defaults": 0}
        for section in ("custom_fields", "select_defaults"):
            existing = config.setdefault(section, [])
            have = {e.get("pattern", "") for e in existing}
            for rule in generated[section]:
                if rule["pattern"] not in have:
                    existing.append(rule)
                    added[section] += 1

    with open(path, "w") as f:
        json.dump(config, f, indent=2)

    return {
        "path": str(path),
        "added": added,
        "total": {
            "custom_fields": len(config.get("custom_fields", [])),
            "select_defaults": len(config.get("select_defaults", [])),
        },
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="Profile to seed")
    parser.add_argument("--reset", action="store_true",
                        help="Rebuild the whole config from the catalog "
                             "(discards your edits)")
    args = parser.parse_args()

    from config import USER_PROFILE, ACTIVE_PROFILE_NAME
    result = seed_form_config(ACTIVE_PROFILE_NAME, USER_PROFILE, reset=args.reset)
    print(f"\n  📝 Form config: {result['path']}")
    print(f"     Added: {result['added']['custom_fields']} field rules, "
          f"{result['added']['select_defaults']} dropdown rules")
    print(f"     Total: {result['total']['custom_fields']} field rules, "
          f"{result['total']['select_defaults']} dropdown rules")
    print("     Review values in the Admin Panel → Form Fill page.")
