# Job Hunter — Test Scenarios

Manual test scenarios by feature area. Run through these before tagging a release.

---

## Automated Test Runner

```bash
python run_tests.py                  # Run all tests (~6 seconds)
python run_tests.py --api            # API scraper smoke tests only
python run_tests.py --browser        # Playwright browser action tests only
python run_tests.py --matcher        # Matcher logic tests only
python run_tests.py --storage        # CSV storage tests only
python run_tests.py --all            # Everything including slow tests
python run_tests.py -v               # Verbose (show tracebacks)
```

**24 tests across 5 categories:**
- **API scrapers (7):** Live HTTP calls to Himalayas, RemoteOK, Greenhouse, Lever, Arbeitnow, USAJobs + format stability check
- **Matcher (4):** Salary parsing, range overlap, keyword matching, exclude keywords
- **Storage (3):** CSV write/read, deduplication, column order
- **Browser (7):** Playwright install, navigation, form detection, form fill, file upload, apply type detection, field pattern matching
- **Config (3):** Admin server exists, form config template, example profile

No profile required — uses standalone test fixtures. Skips tests gracefully when API keys are missing or sources are down.

---

## 1. Profile & Setup

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 1.1 | Profile loads | `python -c "from config import load_profile; load_profile('yourname')"` | No errors, prints config |
| 1.2 | Missing profile | `python run_scrape.py --profile nonexistent` | Clear error: "Profile not found" |
| 1.3 | Resume picker | `python resume_picker.py --profile yourname` | Lists all role types with PDF paths, files exist |
| 1.4 | Example profile unchanged | Diff `example_profile.py` against known template | No personal data in template |

---

## 2. API Scraping (Phase 1A)

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 2.1 | Full scrape | `python run_scrape.py --profile yourname` | Completes in 1-3 min, prints job counts per source |
| 2.2 | Jobs CSV created | `ls output/yourname/jobs.csv` | File exists, has header row + data rows |
| 2.3 | CSV columns correct | Open CSV, check headers | Matches SHEET_COLUMNS: Job Title, Company, Location, Work Type, Salary, Role Category, Match Reason, Apply Method, Apply, Resume Version, URL, Source, Date Found, Date Applied, Notes |
| 2.4 | Deduplication | Run scrape twice | No duplicate URLs in CSV |
| 2.5 | Location filter | Check jobs in CSV | Only Remote + nearby_cities jobs appear |
| 2.6 | Salary filter | Check matched jobs | Salary overlaps with role's salary_min/salary_max range |
| 2.7 | Source down | Disconnect internet for one source | Scraper skips it, continues with others, shows 0 for that source |
| 2.8 | No API keys | Remove all optional keys from .env | Free sources still work (Greenhouse, Lever, Himalayas, RemoteOK, Arbeitnow) |

---

## 3. Browser Scraping (Phase 1B)

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 3.1 | LinkedIn scrape | `python run_scrape_browsers.py --profile yourname` | browser_jobs.csv created with LinkedIn results |
| 3.2 | Browser CSV columns | Open browser_jobs.csv | Has Easy Apply and Direct Apply Link columns |
| 3.3 | Separate file | Check output dir | browser_jobs.csv is separate from jobs.csv |

---

## 4. Auto-Apply (Phase 2)

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 4.1 | Dry run | Mark job Y in CSV, run `python run_apply.py --profile yourname --dry-run` | Browser opens, navigates to job, fills form, does NOT submit |
| 4.2 | Resume selection | Check which PDF is uploaded | Matches role category's resume_file |
| 4.3 | Form fill | Watch browser during apply | Name, email, phone, city filled from profile |
| 4.4 | Custom fields | Add pattern to form_config.json, apply to matching job | Custom field auto-filled |
| 4.5 | Pause before submit | Run without --dry-run | Browser pauses and asks for confirmation before submit |
| 4.6 | Mark done | After successful apply | Apply column changes to "Done" with date |

---

## 5. Admin Panel

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 5.1 | Server starts | `python admin/server.py` | Prints "Open http://localhost:5175" |
| 5.2 | Dashboard loads | Open http://localhost:5175 | Shows job counts, category breakdown |
| 5.3 | Jobs table | Click Jobs tab | Jobs display with Apply buttons |
| 5.4 | Approve job | Click Y button on a job | Job marked Y, toast confirms |
| 5.5 | Reject job | Click Y button again (toggle to N) | Job marked N |
| 5.6 | Search | Type company name in search | Table filters |
| 5.7 | Work type filter | Select "Remote" | Only remote jobs shown |
| 5.8 | Config page | Click Config tab | Profile info, location, roles displayed |
| 5.9 | Form fill edit | Click Form Fill, add pattern, save | form_config.json updated |
| 5.10 | Resumes page | Click Resumes | PDF cards with View links |
| 5.11 | Run scrape | Click "Run API Scrape" on dashboard | Status shows "Running", completes, toast confirms |
| 5.12 | History | Click History | Shows scrape runs with timestamps and status |
| 5.13 | Setup check | Click Setup | Shows Python, venv, deps, profile status |

---

## 6. Admin Panel — Deployed Mode

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 6.1 | Deployed mode starts | `python admin/server.py --deployed` | Badge shows "DEPLOYED", no profile dropdown |
| 6.2 | All users visible | Open dashboard | All profiles shown as expandable sections |
| 6.3 | Expand/collapse | Click user header | Section toggles open/closed |
| 6.4 | Global stats | Check top cards | Total Users, Total Jobs, Approved, Applied aggregated |
| 6.5 | Add user wizard — step 1 | Click "+ Add User", fill name/email/phone/city/state, click Create | Profile .py created, output dirs created, wizard advances to step 2 |
| 6.6 | Add user wizard — step 2 | Click "+ Add Role", fill role ID, label, salary range, search queries, save | Role added to profile's ROLE_PROFILES, appears in role list |
| 6.7 | Add user wizard — add multiple roles | Add 2+ roles in wizard | All roles saved to profile, each shows in role list with salary and queries |
| 6.8 | Add user wizard — remove role | Click Remove on a role in wizard | Role deleted from profile via API, disappears from list |
| 6.9 | Add user wizard — step 3 | Click "Next: Resumes", upload PDF | Resume uploaded to output/{profile}/resumes/, card appears |
| 6.10 | Add user wizard — finish | Click "Done" | Modal closes, new user appears in all pages |
| 6.11 | Resume upload | Expand user in Resumes, click upload area | PDF uploads, appears in grid |
| 6.12 | Resume delete | Click Delete on a resume | File removed, card disappears |
| 6.13 | Per-user scrape | Click "Run API Scrape" under a user | Scrape runs for that user only |

---

## 7. Role Management (Admin API)

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 7.1 | List roles | `GET /api/profiles/{name}/roles` | Returns array of role objects with role_id, label, salary, queries |
| 7.2 | Add role | `POST /api/profiles/{name}/roles` with role JSON | Role added, 200 returned |
| 7.3 | Add role — duplicate ID | POST with existing role_id | 409 or role updated (no crash) |
| 7.4 | Add role — missing queries | POST with empty search_queries | 400 error |
| 7.5 | Update role | `PUT /api/profiles/{name}/roles/{role_id}` with updated fields | Role updated in profile |
| 7.6 | Delete role | `DELETE /api/profiles/{name}/roles/{role_id}` | Role removed from ROLE_PROFILES |
| 7.7 | Delete nonexistent role | DELETE with bad role_id | 404 or graceful no-op |
| 7.8 | Roles persist | Add role via API, reload profile, check ROLE_PROFILES | Role present in .py file |
| 7.9 | Zero roles | Delete all roles from profile | ROLE_PROFILES = {} in file, scrape runs with no results |
| 7.10 | Many roles | Add 10+ roles | All saved, all appear in resume picker and scraper |

---

## 8. Storage Modes

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 7.1 | Local CSV | Set STORAGE_MODE="local", run scrape | output/{profile}/jobs.csv updated |
| 7.2 | Google Sheets | Set STORAGE_MODE="google", configure sheet ID, run scrape | Google Sheet updated |
| 7.3 | Mode switch | Change STORAGE_MODE, run scrape | Writes to new target, old data preserved |

---

## 9. Gig Sources (AI Training & Freelance)

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 9.1 | AI-training directory | `python ai_training.py --profile <p>` | Prints 15 platforms; writes `output/{p}/ai_training.json` |
| 9.2 | AI-training scrape | Profile has `ai-training` role, run scrape | Rows tagged "AI Training / Data Annotation" appear |
| 9.3 | Skip AI | `run_scrape.py --profile <p> --no-ai` | No AI-training sources hit |
| 9.4 | Freelance boards | Role with `freelance_boards: True`, run scrape | Freelancer.com rows + 🔎 saved-search rows appear |
| 9.5 | Hours cap | Role with `max_hours_per_week: 10` | Full-time postings matching the queries are filtered out |
| 9.6 | Skip freelance | `run_scrape.py --profile <p> --no-freelance` | No freelance sources hit |

---

## 10. Quality Filters

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 10.1 | Relevance | Scrape a role; check log | "title unrelated to role keywords" drops off-topic gigs |
| 10.2 | Currency | Freelance scrape with `filter_usd_only` | ₹/€/£ budget rows dropped |
| 10.3 | Min budget | `filter_min_budget: 25`, freelance scrape | Freelancer projects under $25 dropped |
| 10.4 | Aggregators | Web search on | "1,000+ … jobs" listing pages dropped |
| 10.5 | Cross-source dedupe | Same posting on two boards | Only one row kept (title+company key) |
| 10.6 | Retro-clean | `python quality_filter.py --profile <p> --clean --dry-run` | Lists removable rows; approved (Y/Done) rows untouched |

---

## 11. Per-Role Checks

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 11.1 | CLI single role | `run_scrape.py --profile <p> --role <id>` | Only that role scraped/matched; stale cleanup skipped |
| 11.2 | Unknown role | `--role bogus` | Errors with the list of valid role ids, exits cleanly |
| 11.3 | Admin Run Check | Resumes/Config page → **▶ Run Check** | Scrape starts scoped to that role; Jobs page updates |

---

## 12. Auto-fill Field Catalog & Live Form Pass

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 12.1 | Seed catalog | `python ats_fields.py --profile <p>` | ~35 rules written to `form_config.json` |
| 12.2 | Merge (no clobber) | Edit a value, re-run without `--reset` | Edited value preserved; only missing rules added |
| 12.3 | Reset | `python ats_fields.py --profile <p> --reset` | Config rebuilt from catalog |
| 12.4 | Candidate answers | EEO dropdown on a real form | One of the `a\|b\|c` candidates selected |
| 12.5 | Auto-fill against a live form | Headless Playwright load of a real Greenhouse job (e.g. a `job-boards.greenhouse.io/*/jobs/*` URL), run `fill_form_fields` | Identity fields fill; **no personal data lands in free-text screener/EEO questions** (regression check for the screener-question guard) |
| 12.6 | Screener guard | Field label "…require sponsorship at your current location?" | City value is NOT filled in; only an explicit visa/sponsor rule answers it |

---

## 13. Boolean / X-Ray Search

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| 13.1 | Print strings | `python boolean_query.py --profile <p>` | Per role: LinkedIn/ATS Boolean string + one Google X-Ray string per ATS site |
| 13.2 | Boolean composition | Role with `must_have` / `nice_to_have` set | `("titles") AND must AND (nice) NOT exclude` — quoting on multi-word terms |
| 13.3 | Saved-search rows | Run with `boolean_search: True` (or `--xray`) | `jobs.csv` gets 🔎 LinkedIn/Indeed/Google-X-Ray rows, force-matched to the role, kept by the quality filter |
| 13.4 | X-Ray fetch | `python boolean_query.py --profile <p> --fetch` | Real Greenhouse/Lever/Ashby postings when DuckDuckGo cooperates; graceful `0 postings … (throttling)` note otherwise |
| 13.5 | Admin display | Config page → a role card → "🧭 Boolean / X-Ray search strings" | Expands to the Boolean string (Copy button) + LinkedIn/Indeed/X-Ray links |
| 13.6 | Skip flag | `run_scrape.py --profile <p> --no-xray` | Step 1e skipped even when `boolean_search: True` |
