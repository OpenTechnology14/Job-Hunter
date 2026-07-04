"""
Phase 1: Scrape + Match + Push to spreadsheet (local CSV or Google Sheets)

Usage:
    python run_scrape.py --profile alex
    python run_scrape.py --profile alex --web          # Force web search on
    python run_scrape.py --profile alex --no-web       # Force web search off
    python run_scrape.py --profile alex --no-cleanup   # Skip stale job removal
    python run_scrape.py --profile alex --browsers     # Also scrape LinkedIn + Indeed
    python run_scrape.py --profile alex --no-browsers  # Skip browser scrape (default)
"""
import json
import argparse
from datetime import datetime

from scraper import scrape_all_jobs
from matcher import match_jobs
from storage import push_jobs, cleanup_stale_jobs
from config import DATA_DIR, STORAGE_MODE, PROFILE_DIR, ROLE_PROFILES, SEARCH_SETTINGS


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="Profile to use")
    parser.add_argument("--web", action="store_true",
                        help="Force web search on (overrides profile setting)")
    parser.add_argument("--no-web", action="store_true",
                        help="Force web search off (overrides profile setting)")
    parser.add_argument("--no-cleanup", action="store_true",
                        help="Skip removal of stale unapproved jobs")
    parser.add_argument("--no-ai", action="store_true",
                        help="Skip AI-training sources even if the profile has an ai-training role")
    parser.add_argument("--browsers", action="store_true",
                        help="Also run LinkedIn + Indeed browser scrape (Phase 1B)")
    parser.add_argument("--no-browsers", action="store_true",
                        help="Skip browser scrape even if profile enables it")
    args = parser.parse_args()

    print(f"\n🔍 Phase 1: Scrape & Match")
    print(f"{'='*60}")

    # ── Step 0: Clean up stale jobs ──────────────────────
    if not args.no_cleanup:
        cleanup_stale_jobs()

    # ── Step 1: Scrape job boards ────────────────────────
    raw_jobs = scrape_all_jobs()

    # ── Step 1b: Web search (optional) ───────────────────
    if args.no_web:
        web_enabled = False
    else:
        web_enabled = args.web or SEARCH_SETTINGS.get("web_search", False)
    if web_enabled:
        try:
            from scraper_web import scrape_web_sources
            from dataclasses import asdict as _asdict

            # Gather all search queries from all roles
            all_queries = []
            for role in ROLE_PROFILES.values():
                all_queries.extend(role["search_queries"])
            all_queries = list(set(all_queries))  # Dedupe

            locations = SEARCH_SETTINGS.get("locations", ["Remote"])
            location = locations[0] if locations else "Remote"
            max_per = SEARCH_SETTINGS.get("max_results_per_query", 25)

            web_jobs = scrape_web_sources(all_queries, location, max_results=max_per * 2)
            raw_jobs.extend(web_jobs)
            print(f"\n  🌐 Web search added {len(web_jobs)} jobs to the pipeline")
        except ImportError as e:
            print(f"\n  ⚠️  Web search skipped: {e}")
        except Exception as e:
            print(f"\n  ⚠️  Web search error: {e}")

    # ── Step 1c: AI-training sources (optional) ──────────
    # Runs when the profile has an "ai-training" role. Scrapes AI-training
    # company boards (Ashby/Greenhouse/Lever) for trainer/annotation roles.
    if "ai-training" in ROLE_PROFILES and not args.no_ai:
        try:
            from ai_training import scrape_ai_training_sources
            ai_jobs = scrape_ai_training_sources(
                max_results=SEARCH_SETTINGS.get("max_results_per_query", 25) * 2)
            raw_jobs.extend(ai_jobs)
            print(f"\n  🤖 AI-training sources added {len(ai_jobs)} jobs to the pipeline")
        except ImportError as e:
            print(f"\n  ⚠️  AI-training sources skipped: {e}")
        except Exception as e:
            print(f"\n  ⚠️  AI-training sources error: {e}")

    # ── Step 2: Match (keyword + salary, no AI) ──────────
    from dataclasses import asdict
    raw_dicts = []
    for j in raw_jobs:
        raw_dicts.append(asdict(j) if hasattr(j, '__dataclass_fields__') else j)

    matched = match_jobs(raw_dicts)

    # Save matched results locally
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    out = DATA_DIR / f"matched_jobs_{timestamp}.json"
    with open(out, "w") as f:
        json.dump(matched, f, indent=2)
    print(f"\n  Saved matched jobs: {out}")

    # ── Step 3: Push to spreadsheet ──────────────────────
    print(f"\n  Pushing to {'Google Sheet' if STORAGE_MODE == 'google' else 'local CSV'}...")
    push_jobs(matched)

    if STORAGE_MODE == "local":
        print(f"\n  📄 Open in your spreadsheet app: {PROFILE_DIR / 'jobs.csv'}")

    # ── Step 4: Browser scrape — LinkedIn + Indeed (optional) ──
    browser_scrape = False
    if args.no_browsers:
        browser_scrape = False
    elif args.browsers:
        browser_scrape = True
    else:
        browser_scrape = SEARCH_SETTINGS.get("browser_scrape", False)

    if browser_scrape:
        try:
            from run_scrape_browsers import run_browser_scrape
            print(f"\n{'='*60}")
            print(f"  🌐 Phase 1B: Browser Scrape (LinkedIn + Indeed)")
            print(f"{'='*60}")
            run_browser_scrape()
        except ImportError as e:
            print(f"\n  ⚠️  Browser scrape skipped: {e}")
            print(f"      Install Playwright: pip install playwright && playwright install chromium")
        except Exception as e:
            print(f"\n  ⚠️  Browser scrape error: {e}")

    print(f"\n{'='*60}")
    print(f"  ✅ Done! Review the spreadsheet, then mark jobs as")
    print(f"     '✅ Ready to Apply' and run: python run_apply.py --profile <name>")
    print(f"{'='*60}")


if __name__ == "__main__":
    run()
