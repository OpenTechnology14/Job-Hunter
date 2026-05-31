"""
Resume Picker — maps role categories to pre-made resume PDFs.

Usage:
    python resume_picker.py --profile alex    # verify files
"""
import argparse
from pathlib import Path
from config import ROLE_PROFILES, INTERESTING_ROLE, RESUMES_DIR


def get_resume_for_role(role_id: str) -> str:
    role = ROLE_PROFILES.get(role_id, {})
    filename = role.get("resume_file", "")
    if filename:
        path = RESUMES_DIR / filename
        if path.exists():
            return str(path)

    fallback = INTERESTING_ROLE.get("resume_file", "")
    if fallback:
        path = RESUMES_DIR / fallback
        if path.exists():
            return str(path)

    pdfs = list(RESUMES_DIR.glob("*.pdf"))
    if pdfs:
        return str(pdfs[0])

    print(f"    ❌ No resume files in {RESUMES_DIR}/")
    return ""


def get_resume_by_filename(filename: str) -> str:
    if filename:
        path = RESUMES_DIR / filename
        if path.exists():
            return str(path)
    return get_resume_for_role("interesting")


def verify_setup():
    print(f"\nResume directory: {RESUMES_DIR}/")
    print(f"{'─'*60}")

    all_good = True
    for role_id, role in ROLE_PROFILES.items():
        filename = role.get("resume_file", "")
        label = role.get("label", role_id)
        sal = f"${role.get('salary_min',0):,} – ${role.get('salary_max',0):,}"

        if not filename:
            print(f"  ⚠️  {label:35s} → no resume_file set")
            all_good = False
            continue

        path = RESUMES_DIR / filename
        if path.exists():
            kb = path.stat().st_size / 1024
            print(f"  ✅ {label:35s} → {filename} ({kb:.0f}KB)  |  {sal}")
        else:
            print(f"  ❌ {label:35s} → {filename} (NOT FOUND)  |  {sal}")
            all_good = False

    fb = INTERESTING_ROLE.get("resume_file", "")
    if fb:
        path = RESUMES_DIR / fb
        status = "✅" if path.exists() else "❌"
        i_sal = f"${INTERESTING_ROLE.get('salary_min',0):,} – ${INTERESTING_ROLE.get('salary_max',0):,}"
        print(f"  {status} {'Fallback':35s} → {fb}  |  {i_sal}")
        if not path.exists():
            all_good = False

    pdfs = list(RESUMES_DIR.glob("*.pdf"))
    if pdfs:
        print(f"\n  PDFs found:")
        for p in pdfs:
            print(f"    📄 {p.name}")
    else:
        print(f"\n  ⚠️  Drop your PDFs in: {RESUMES_DIR}/")

    print(f"\n  {'✅ All good!' if all_good else '❌ Missing files above'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="Profile to check")
    verify_setup()
