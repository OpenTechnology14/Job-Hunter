"""
Phase 2: Apply to jobs marked "Ready to Apply" in the Google Sheet.

Usage:
    python run_apply.py --profile alex
    python run_apply.py --profile alex --dry-run
"""
import argparse
from resume_picker import verify_setup
from browser_apply import run_apply_session


def run(dry_run: bool = False):
    print(f"\n🚀 Phase 2: Apply to Ready Jobs")
    print(f"{'='*60}")

    print("\n  Checking resume files...")
    verify_setup()

    print()
    run_apply_session(dry_run=dry_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="Profile to use")
    parser.add_argument("--dry-run", action="store_true",
                        help="Open browser, fill forms, but don't submit anything")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
