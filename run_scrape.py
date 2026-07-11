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
    parser.add_argument("--no-freelance", action="store_true",
                        help="Skip freelance boards even if a role enables freelance_boards")
    parser.add_argument("--xray", action="store_true",
                        help="Force Boolean/X-Ray search on (overrides profile setting)")
    parser.add_argument("--no-xray", action="store_true",
                        help="Skip Boolean/X-Ray search even if boolean_search is on")
    parser.add_argument("--role", action="append",
                        help="Run the check for a single role id only (repeatable, "
                             "e.g. --role it-automation-contractor). Scopes scraping, "
                             "matching, web/AI/freelance sources to that role.")
    parser.add_argument("--browsers", action="store_true",
                        help="Also run LinkedIn + Indeed browser scrape (Phase 1B)")
    parser.add_argument("--no-browsers", action="store_true",
                        help="Skip browser scrape even if profile enables it")
    args = parser.parse_args()

    print(f"\n🔍 Phase 1: Scrape & Match")
    print(f"{'='*60}")

    # ── Role filter: individual check for selected role(s) ──
    # ROLE_PROFILES is the same dict object imported by scraper, matcher,
    # and the browser scraper, so filtering it in place scopes every
    # downstream step to the selected role(s).
    if args.role:
        unknown = [r for r in args.role if r not in ROLE_PROFILES]
        if unknown:
            print(f"\n❌ Unknown role(s): {', '.join(unknown)}")
            print(f"   Available: {', '.join(ROLE_PROFILES)}")
            return
        keep = set(args.role)
        for rid in [r for r in ROLE_PROFILES if r not in keep]:
            del ROLE_PROFILES[rid]
        print(f"  🎯 Individual check — role(s): {', '.join(keep)}")

    # ── Step 0: Clean up stale jobs ──────────────────────
    # Skipped on individual checks: a targeted run shouldn't delete
    # other roles' rows that this run won't re-scrape.
    if args.role:
        if not args.no_cleanup:
            print("  (stale cleanup skipped — targeted role check)")
    elif not args.no_cleanup:
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

    # ── Step 1d: Freelance boards (optional) ─────────────
    # Runs for every role with "freelance_boards": True. Scrapes the
    # Freelancer.com API (hour-capped) and writes saved part-time search
    # rows for bot-blocked boards (Upwork, PeoplePerHour, Guru, Braintrust).
    freelance_roles = {rid: r for rid, r in ROLE_PROFILES.items()
                       if r.get("freelance_boards")}
    if freelance_roles and not args.no_freelance:
        try:
            from scraper_freelance import scrape_freelance_sources
            for rid, role in freelance_roles.items():
                fl_jobs = scrape_freelance_sources(
                    role["search_queries"], rid,
                    max_hours=role.get("max_hours_per_week", 0),
                    max_results=SEARCH_SETTINGS.get("max_results_per_query", 25),
                )
                raw_jobs.extend(fl_jobs)
                print(f"\n  💼 Freelance boards added {len(fl_jobs)} rows for '{rid}'")
        except ImportError as e:
            print(f"\n  ⚠️  Freelance boards skipped: {e}")
        except Exception as e:
            print(f"\n  ⚠️  Freelance boards error: {e}")

    # ── Step 1e: Boolean / X-Ray search (optional) ───────
    # Adds clickable LinkedIn/Google-X-Ray/Indeed Boolean rows per role and
    # best-effort fetches ATS postings via X-Ray (companies not in the slug
    # lists). Enabled by boolean_search in SEARCH_SETTINGS or --xray.
    if args.no_xray:
        xray_enabled = False
    else:
        xray_enabled = args.xray or SEARCH_SETTINGS.get("boolean_search", False)
    if xray_enabled:
        try:
            from boolean_query import scrape_boolean_sources
            locations = SEARCH_SETTINGS.get("locations", ["Remote"])
            location = locations[0] if locations else "Remote"
            bq_jobs = scrape_boolean_sources(
                ROLE_PROFILES, location, do_fetch=True,
                max_results=SEARCH_SETTINGS.get("max_results_per_query", 25),
                default_exclude=SEARCH_SETTINGS.get("exclude_keywords", []),
            )
            raw_jobs.extend(bq_jobs)
            print(f"\n  🧭 Boolean/X-Ray search added {len(bq_jobs)} rows to the pipeline")
        except ImportError as e:
            print(f"\n  ⚠️  Boolean/X-Ray search skipped: {e}")
        except Exception as e:
            print(f"\n  ⚠️  Boolean/X-Ray search error: {e}")

    # ── Step 2: Match (keyword + salary, no AI) ──────────
    from dataclasses import asdict
    raw_dicts = []
    for j in raw_jobs:
        raw_dicts.append(asdict(j) if hasattr(j, '__dataclass_fields__') else j)

    matched = match_jobs(raw_dicts)

    # Individual check: keep only the selected role(s). The usual
    # "Unmatched — Review" pass-through is noise here — those titles
    # came from this role's queries but didn't fit its filters.
    if args.role:
        before = len(matched)
        matched = [m for m in matched if m["role_category"] in set(args.role)]
        if before != len(matched):
            print(f"  🎯 Role filter: kept {len(matched)}/{before} matched jobs")

    # ── Step 2b: Quality filters ─────────────────────────
    # Relevance, currency/budget, aggregator-page, and duplicate hygiene.
    # Config-driven — see quality_filter.py and the Config page toggles.
    try:
        from quality_filter import apply_quality_filters
        matched = apply_quality_filters(matched)
    except ImportError as e:
        print(f"\n  ⚠️  Quality filters skipped: {e}")

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
