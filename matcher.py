"""
Job Matcher (No AI Required)
Matches scraped jobs to role types using keyword matching and salary filtering.

Logic:
  1. Match job title against each role's search_queries (fuzzy keyword match)
  2. If job has a listed salary, check it overlaps with the role's salary range
  3. If job has no salary, it passes salary check (you review in the sheet)
  4. Assign role category, resume version, and match reason
  5. Filter out excluded keywords

Usage:
    from matcher import match_jobs
    matched = match_jobs(raw_jobs)
"""
import re
from config import ROLE_PROFILES, SEARCH_SETTINGS, INTERESTING_ROLE


def parse_salary(salary_str: str) -> tuple[int, int]:
    """
    Extract min and max salary from a salary string.
    Handles: "$80,000 - $120,000", "$95k-$120k", "$80000", etc.
    Returns (0, 0) if unparseable.
    """
    if not salary_str:
        return 0, 0

    # Find all dollar amounts
    amounts = re.findall(r'\$?([\d,]+(?:\.\d+)?)\s*[kK]?', salary_str)
    if not amounts:
        return 0, 0

    parsed = []
    for amt in amounts:
        num = float(amt.replace(",", ""))
        # Detect "k" notation
        if re.search(r'\d\s*[kK]', salary_str) and num < 1000:
            num *= 1000
        parsed.append(int(num))

    if len(parsed) >= 2:
        return min(parsed), max(parsed)
    elif len(parsed) == 1:
        return parsed[0], parsed[0]
    return 0, 0


def salary_in_range(job_salary: str, role_min: int, role_max: int) -> tuple[bool, str]:
    """
    Check if a job's salary overlaps with the role's target range.
    Returns (passes, reason).
    """
    sal_min, sal_max = parse_salary(job_salary)

    # No salary listed — pass it through, user can judge
    if sal_min == 0 and sal_max == 0:
        return True, "No salary listed"

    # Check for overlap: job's range overlaps role's range
    if sal_max < role_min:
        return False, f"Below range (${sal_max:,} < ${role_min:,})"
    if sal_min > role_max:
        return False, f"Above range (${sal_min:,} > ${role_max:,})"

    return True, f"${sal_min:,}-${sal_max:,} fits ${role_min:,}-${role_max:,}"


def match_title_to_role(title: str) -> tuple[str, str, float]:
    """
    Match a job title to a role profile using keyword matching.
    Returns (role_id, role_label, confidence).
    """
    title_lower = title.lower()
    best_role_id = ""
    best_label = ""
    best_score = 0.0

    for role_id, role in ROLE_PROFILES.items():
        for query in role["search_queries"]:
            query_lower = query.lower()
            query_words = query_lower.split()

            # Exact substring match (strongest)
            if query_lower in title_lower:
                score = 1.0
            # All words present in title
            elif all(w in title_lower for w in query_words):
                score = 0.8
            # Most words present
            elif sum(1 for w in query_words if w in title_lower) / len(query_words) > 0.6:
                score = 0.5
            else:
                continue

            if score > best_score:
                best_score = score
                best_role_id = role_id
                best_label = role["label"]

    return best_role_id, best_label, best_score


def match_jobs(jobs: list[dict]) -> list[dict]:
    """
    Match and filter a list of scraped jobs.
    Returns jobs that pass keyword + salary filtering.
    """
    matched = []
    excluded = SEARCH_SETTINGS.get("exclude_keywords", [])
    excluded_lower = [kw.lower() for kw in excluded]

    for job in jobs:
        title = job.get("title", "")
        salary = job.get("salary", "")

        # Skip excluded keywords
        title_lower = title.lower()
        if any(ex in title_lower for ex in excluded_lower):
            continue

        # Scraper-provided role hint (e.g. AI-training sources) wins outright
        role_hint = job.get("role_hint", "")
        if role_hint and role_hint in ROLE_PROFILES:
            role_id = role_hint
            role_label = ROLE_PROFILES[role_hint]["label"]
            confidence = 1.0
        else:
            # Match title to role
            role_id, role_label, confidence = match_title_to_role(title)

        if not role_id:
            # No role match — tag as "Unmatched" for manual review
            role_id = "unmatched"
            role_label = "Unmatched — Review"
            sal_pass = True
            sal_reason = "No role match"
            resume_file = INTERESTING_ROLE.get("resume_file", "")
        else:
            # Check salary range
            role = ROLE_PROFILES[role_id]
            sal_pass, sal_reason = salary_in_range(
                salary, role["salary_min"], role["salary_max"]
            )
            resume_file = role.get("resume_file", "")

        if not sal_pass:
            continue  # Salary out of range, skip

        job_out = job.copy()
        job_out.update({
            "role_category": role_id,
            "role_category_label": role_label,
            "match_reason": sal_reason,
            "recommended_resume": resume_file,
            "status": "🔍 New",
        })
        matched.append(job_out)

    # Sort: matched roles first, then unmatched
    matched.sort(key=lambda j: (
        0 if j["role_category"] != "unmatched" else 1,
        j.get("role_category_label", ""),
    ))

    print(f"\n  Matched: {len(matched)} / {len(jobs)} jobs passed filters")

    # Breakdown
    cats = {}
    for j in matched:
        cat = j["role_category_label"]
        cats[cat] = cats.get(cat, 0) + 1
    for cat, count in sorted(cats.items(), key=lambda x: x[1], reverse=True):
        print(f"    {cat}: {count}")

    return matched
