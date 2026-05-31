# Admin Panel UI — Build Specification

## Current Status: V1 BUILT AND WORKING

The lightweight admin panel is live at `admin/server.py`. Start it with:

```bash
source venv/bin/activate
python admin/server.py
# Open http://localhost:5175
```

**V1 Stack:** Python (Flask) backend + vanilla HTML/JS frontend. No build step.
No Node.js required. Single `python admin/server.py` command.

**V1 Features working:**
- Dashboard with job stats, category breakdown, scrape buttons
- Job Board with inline Y/N approval, search, filters, sorting, API/Browser tabs
- Configuration viewer (profile info, location filter, role profiles)
- Form Fill editor (custom field patterns, select defaults, save to JSON)
- Resume viewer with PDF links
- Run History log
- Setup Checklist with auto-detection

**V2 (optional future upgrade):** The spec below describes a React + TypeScript
version with more interactive features (drag-drop, inline editing, etc.). Only
build this if the V1 Flask version is insufficient.

---

## V2 Spec: React + TypeScript + Vite (Optional)

This is the full build spec for a React-based admin panel. This is an
**alternative to the working V1** — only build this if you need features
beyond what the Flask admin provides.

**Stack:** React + TypeScript + Vite (frontend) + Express (backend API wrapping
the existing Python scripts). Runs locally alongside the existing system.

---

## Architecture

```
Browser (localhost:5174)
   │
   ├── Admin Panel (React SPA)
   │     ├── Setup Wizard        ← Interactive checklist
   │     ├── Job Board           ← Approve/reject jobs
   │     ├── Run History         ← Scrape/apply logs
   │     ├── Configuration       ← Profiles, locations, sources
   │     ├── Form Fill Config    ← Auto-fill field mappings
   │     └── Resume Manager      ← Upload/assign PDFs
   │
   └── API Server (Express, localhost:5175)
         ├── /api/profiles       ← CRUD profile configs
         ├── /api/jobs           ← Read/update CSV data
         ├── /api/scrape         ← Trigger scrape runs
         ├── /api/apply          ← Trigger apply runs
         ├── /api/history        ← Run logs
         ├── /api/form-config    ← Form fill mappings
         ├── /api/resumes        ← Upload/list PDFs
         └── /api/setup          ← Checklist state
```

The Express server calls Python scripts via child_process (e.g. `python
run_scrape.py --profile alex`) and reads/writes the existing CSV and JSON files.
No database needed — the filesystem IS the database.

---

## Pages

### 1. Setup Wizard (`/setup`)

Interactive version of SETUP_CHECKLIST.md. Each step is a card that either:
- **Auto-checks** (Python version, venv exists, dependencies installed)
- **Provides a form** (create profile, set location filter)
- **Runs a command** (install deps, first scrape)

State is stored in `output/.setup_state.json`.

```
┌─────────────────────────────────────────────────────┐
│  Setup Wizard                          Progress 6/12│
├─────────────────────────────────────────────────────┤
│                                                     │
│  ✅ Python 3.12 installed                           │
│  ✅ Virtual environment created                     │
│  ✅ Dependencies installed                          │
│  ✅ Playwright + Chromium ready                     │
│  ✅ Profile: alex configured                        │
│  🔄 Profile: marcelli — resumes needed              │
│     [Upload Resume PDFs]                            │
│  ⬜ API Keys (optional)                             │
│     [Configure API Keys]                            │
│  ⬜ First scrape run                                │
│     [Run Scrape Now]                                │
│  ⬜ Form fill config                                │
│     [Configure Form Fields]                         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**API endpoints:**
- `GET /api/setup` — returns checklist with auto-detected states
- `POST /api/setup/run-step` — execute a setup step (install, scrape, etc.)

---

### 2. Job Board (`/jobs`)

Main working page. Two tabs: **API Jobs** (`jobs.csv`) and **Browser Jobs**
(`browser_jobs.csv`).

```
┌─────────────────────────────────────────────────────────────────┐
│  Job Board              Profile: [alex ▾]    [Scrape Now ▾]    │
├──────────┬──────────────────────────────────────────────────────┤
│ Filters  │ ┌─────────────────────────────────────────────────┐  │
│          │ │ [API Jobs]  [LinkedIn/Indeed]                    │  │
│ Work Type│ ├───────┬──────────┬─────────┬────────┬──────┬────┤  │
│ ☑ Remote │ │ Apply │ Title    │ Company │Location│Salary│... │  │
│ ☑ On-site│ ├───────┼──────────┼─────────┼────────┼──────┼────┤  │
│ ☑ Hybrid │ │  [Y]  │ AI Eng   │ Acme    │ Remote │ 120k │    │  │
│          │ │  [N]  │ DevOps   │ BigCo   │ Nashua │ 110k │    │  │
│ Category │ │  [ ]  │ Sec Ops  │ CyberX  │ Remote │ 95k  │    │  │
│ ☑ All    │ │  [Y]  │ ML Eng   │ StartUp │ Lowell │ 130k │    │  │
│          │ ├───────┴──────────┴─────────┴────────┴──────┴────┤  │
│ Source   │ │ Showing 94 jobs · 3 approved · 0 applied        │  │
│ ☑ All    │ └─────────────────────────────────────────────────┘  │
│          │                                                      │
│ Salary   │ Actions:                                             │
│ [min]-   │ [Apply to Approved (3)] [Export CSV] [Clear Applied] │
│     [max]│                                                      │
└──────────┴──────────────────────────────────────────────────────┘
```

**Features:**
- Click Y/N in Apply column to approve/reject inline
- Bulk select with checkboxes
- Filter by Work Type, Category, Source, Salary range
- Sort by any column
- "Scrape Now" dropdown: API Scrape / Browser Scrape / Both
- "Apply to Approved" triggers `run_apply.py` for API jobs
- LinkedIn/Indeed tab shows Easy Apply badge and Direct Apply Link
- LinkedIn/Indeed approved jobs show instruction: "Use Claude Chrome Extension"

**Browser Jobs tab extra columns:**
- Easy Apply: Yes/No/Check
- Direct Apply Link: clickable URL
- Apply: Y/N (same approval system)
- Note at top: "These jobs require manual application. Use Claude Chrome
  Extension for approved jobs — open the job URL, let Claude fill the form."

**API endpoints:**
- `GET /api/jobs?profile=alex&source=api` — list jobs from CSV
- `PATCH /api/jobs/:index` — update Apply column
- `POST /api/jobs/bulk-approve` — approve multiple
- `GET /api/jobs?profile=alex&source=browser` — browser_jobs.csv

---

### 3. Run History (`/history`)

Log of all scrape and apply runs with results.

```
┌──────────────────────────────────────────────────────┐
│  Run History                    Profile: [alex ▾]    │
├──────────┬──────┬───────┬───────┬────────────────────┤
│ Date     │ Type │ Jobs  │ New   │ Status             │
├──────────┼──────┼───────┼───────┼────────────────────┤
│ May 17   │ API  │ 620   │ 94    │ ✅ Complete        │
│ May 17   │ Brws │ 45    │ 38    │ ✅ Complete        │
│ May 16   │ API  │ 580   │ 101   │ ✅ Complete        │
│ May 16   │ Apply│ 3     │ —     │ ✅ 2 applied       │
└──────────┴──────┴───────┴───────┴────────────────────┘

Run details panel (click a row):
  Sources: Himalayas(487), Greenhouse(109), Arbeitnow(17)...
  Matched: 576/620
  Filtered by location: 94 kept, 499 dropped
  Duration: 2m 14s
  Log output: [View Full Log]
```

**Data source:** Parse existing JSON files in `output/{profile}/data/` plus
a new `output/{profile}/run_log.json` that the scrape/apply scripts append to.

**API endpoints:**
- `GET /api/history?profile=alex` — list runs
- `GET /api/history/:id` — run details + log

---

### 4. Configuration (`/config`)

Edit all profile settings without touching Python files.

**Sub-sections:**

#### 4a. Profile Settings
```
┌──────────────────────────────────────────┐
│  Profile: alex                           │
├──────────────────────────────────────────┤
│  Name:    [Alexander Moody         ]     │
│  Email:   [alexmoody1421@gmail.com ]     │
│  Phone:   [(603) 943-0051         ]      │
│  City:    [Nashua    ] State: [NH]       │
│                                          │
│  Skills:  [IT Support, Access Control,   │
│            SaaS Identity, ...]           │
│                                          │
│  [Save Changes]                          │
└──────────────────────────────────────────┘
```

#### 4b. Role Types
```
┌────────────────────────────────────────────────────┐
│  Role Types                        [+ Add Role]   │
├────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐  │
│  │ Cybersecurity / IT Security                  │  │
│  │ Salary: $85,000 - $150,000                   │  │
│  │ Resume: Alex_Moody_Cybersecurity_Resume.pdf  │  │
│  │ Queries: Cybersecurity Analyst, IT Security  │  │
│  │          Analyst, Security Engineer, ...     │  │
│  │ [Edit] [Delete]                              │  │
│  └──────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────┐  │
│  │ AI / Automation Engineer                     │  │
│  │ ...                                          │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

#### 4c. Location Filter
```
┌────────────────────────────────────────────────────┐
│  Location Filter                                   │
├────────────────────────────────────────────────────┤
│  Center:  [Nashua], [NH]                           │
│  Radius:  [20] miles                               │
│  Include Remote: [✅]                              │
│                                                    │
│  Nearby Cities (within radius):                    │
│  [Manchester] [Merrimack] [Hudson] [Lowell]        │
│  [Chelmsford] [Londonderry] [Bedford] [Dracut]     │
│  [+ Add City]                                      │
│                                                    │
│  ⓘ Jobs from locations not in this list and not    │
│    marked Remote will be excluded from scrape      │
│    results.                                        │
│                                                    │
│  [Save Changes]                                    │
└────────────────────────────────────────────────────┘
```

#### 4d. Job Sources
```
┌────────────────────────────────────────────────────┐
│  Job Sources                                       │
├────────────────────────────────────────────────────┤
│  API Sources (run_scrape.py):                      │
│  ✅ Himalayas        (no setup needed)             │
│  ✅ RemoteOK         (no setup needed)             │
│  ✅ Greenhouse       (no setup needed) [Edit Cos]  │
│  ✅ Lever            (no setup needed) [Edit Cos]  │
│  ✅ Arbeitnow        (no setup needed)             │
│  ⬜ USAJobs          [Add API Key]                 │
│  ✅ The Muse         (no setup needed)             │
│  ✅ Wellfound        (no setup needed)             │
│  ⬜ Adzuna           [Add API Key]                 │
│  ⬜ Google Jobs      [Add API Key] (paid)          │
│  ⬜ Workday          [Add Companies]               │
│                                                    │
│  Browser Sources (run_scrape_browsers.py):         │
│  ✅ LinkedIn          (Playwright)                 │
│  ✅ Indeed            (Playwright)                  │
│                                                    │
│  Extended Playwright (run with API scrape):        │
│  ⬜ Dice              [Enable]                     │
│  ⬜ ZipRecruiter      [Enable]                     │
│  ⬜ SimplyHired       [Enable]                     │
│  ⬜ Health eCareers   [Enable]                     │
└────────────────────────────────────────────────────┘
```

**API endpoints:**
- `GET /api/profiles` — list profiles
- `GET /api/profiles/:name` — full profile config
- `PUT /api/profiles/:name` — update profile
- `GET /api/profiles/:name/location` — location filter
- `PUT /api/profiles/:name/location` — update location filter
- `GET /api/sources` — source status (enabled, has key, etc.)
- `PUT /api/sources/:name` — toggle source, update config

---

### 5. Form Fill Config (`/forms`)

Configure what auto-apply fills into job application forms. This replaces the
hardcoded `FIELD_PATTERNS` and `AUTOFILL_DATA` in `browser_apply.py`.

```
┌───────────────────────────────────────────────────────────┐
│  Form Fill Configuration           Profile: [alex ▾]     │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  Standard Fields (auto-detected from profile):            │
│  ┌─────────────────┬──────────────────────┬────────────┐  │
│  │ Form Label      │ Value                │ Enabled    │  │
│  ├─────────────────┼──────────────────────┼────────────┤  │
│  │ First Name      │ Alexander            │ ✅         │  │
│  │ Last Name       │ Moody                │ ✅         │  │
│  │ Email           │ alexmoody1421@...    │ ✅         │  │
│  │ Phone           │ (603) 943-0051       │ ✅         │  │
│  │ LinkedIn        │                      │ ⬜         │  │
│  │ Website         │ opentechnologyblog.. │ ✅         │  │
│  │ City            │ Nashua               │ ✅         │  │
│  │ State           │ NH                   │ ✅         │  │
│  │ Country         │ United States        │ ✅         │  │
│  │ Current Company │ Eleanor Health       │ ✅         │  │
│  │ Current Title   │ Senior IT Support... │ ✅         │  │
│  │ Years Exp       │ 4                    │ ✅         │  │
│  └─────────────────┴──────────────────────┴────────────┘  │
│                                                           │
│  Custom Field Mappings:                    [+ Add Rule]   │
│  ┌────────────────────────┬─────────────────┬──────────┐  │
│  │ Pattern (regex)        │ Fill Value      │          │  │
│  ├────────────────────────┼─────────────────┼──────────┤  │
│  │ salary.?expect         │ Negotiable      │ [Delete] │  │
│  │ earliest.?start        │ Immediately     │ [Delete] │  │
│  │ relocat                │ No              │ [Delete] │  │
│  │ sponsor                │ N/A - US Citizen│ [Delete] │  │
│  │ how.?hear              │ Online search   │ [Delete] │  │
│  │ cover.?letter          │ (skip)          │ [Delete] │  │
│  └────────────────────────┴─────────────────┴──────────┘  │
│                                                           │
│  Dropdown / Select Defaults:               [+ Add Rule]   │
│  ┌────────────────────────┬─────────────────┬──────────┐  │
│  │ Pattern (regex)        │ Preferred Value │          │  │
│  ├────────────────────────┼─────────────────┼──────────┤  │
│  │ gender                 │ Prefer not to.. │ [Delete] │  │
│  │ race|ethnicity         │ Prefer not to.. │ [Delete] │  │
│  │ veteran                │ No              │ [Delete] │  │
│  │ disability             │ Prefer not to.. │ [Delete] │  │
│  │ education.?level       │ Bachelor's      │ [Delete] │  │
│  │ work.?auth             │ Yes             │ [Delete] │  │
│  └────────────────────────┴─────────────────┴──────────┘  │
│                                                           │
│  [Save Changes]  [Reset to Defaults]  [Test on URL...]    │
│                                                           │
│  "Test on URL" opens a Playwright browser, navigates to   │
│  the URL, and shows which fields were filled and which    │
│  were missed — without submitting anything.               │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

**Data source:** `output/{profile}/form_config.json`

**API endpoints:**
- `GET /api/form-config/:profile` — current config
- `PUT /api/form-config/:profile` — update config
- `POST /api/form-config/:profile/test` — dry-run on a URL, return field report

---

### 6. Resume Manager (`/resumes`)

Upload, preview, and assign resume PDFs to role types.

```
┌───────────────────────────────────────────────────────────┐
│  Resume Manager                    Profile: [alex ▾]     │
├───────────────────────────────────────────────────────────┤
│                                                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 📄 Alex_Moody_Cybersecurity_Resume.pdf    50KB     │  │
│  │    Assigned to: Cybersecurity / IT Security         │  │
│  │    [Preview] [Replace] [Download]                   │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 📄 Alex_Moody_AIEngineer_Resume.pdf       50KB     │  │
│  │    Assigned to: AI / Automation Engineer            │  │
│  │    Also: Fallback resume                            │  │
│  │    [Preview] [Replace] [Download]                   │  │
│  └─────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 📄 Alex_Moody_HealthIT_Resume.pdf         50KB     │  │
│  │    Assigned to: Health IT / Clinical Systems        │  │
│  │    [Preview] [Replace] [Download]                   │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  [Upload New Resume]                                      │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

**API endpoints:**
- `GET /api/resumes/:profile` — list PDFs with assignments
- `POST /api/resumes/:profile/upload` — upload new PDF
- `DELETE /api/resumes/:profile/:filename` — remove PDF

---

## Navigation

```
┌──────────────────────────────────────────┐
│  Job Hunter Admin     Profile: [alex ▾]  │
├──────┬──────┬────────┬───────┬──────┬────┤
│Setup │ Jobs │History │Config │Forms │ CV │
└──────┴──────┴────────┴───────┴──────┴────┘
```

- **Setup** — Interactive checklist wizard
- **Jobs** — View, filter, approve/reject jobs (both CSVs)
- **History** — Past scrape/apply run logs
- **Config** — Profile, location, sources, roles
- **Forms** — Form fill field mappings
- **CV** — Resume upload and assignment

---

## Implementation Plan

### Phase 1: Backend API (Express)
1. Create `admin/server.ts` — Express server on port 5175
2. CSV read/write endpoints (reuse local_sync.py logic via Python subprocess)
3. Profile read/write (parse/generate Python profile files)
4. Scrape/apply trigger endpoints (spawn Python processes, stream output)
5. Run log system (`output/{profile}/run_log.json`)

### Phase 2: Frontend Shell (React + Vite)
1. Create `admin/` directory with Vite + React + TypeScript + Tailwind
2. Layout with sidebar nav, profile selector
3. Stub pages with routing

### Phase 3: Job Board Page
1. CSV table with inline Apply toggle
2. Filters (work type, category, source, salary)
3. Column sorting
4. Tab for API jobs vs browser jobs
5. "Scrape Now" button

### Phase 4: Configuration Page
1. Profile editor form
2. Role type CRUD
3. Location filter editor with city list
4. Source toggle panel

### Phase 5: Form Fill Config
1. Load/save form_config.json
2. Standard fields from profile
3. Custom regex pattern → value mapping
4. Dropdown/select defaults
5. "Test on URL" dry-run

### Phase 6: Setup Wizard
1. Auto-detect checklist state
2. Step-by-step interactive cards
3. Run commands from UI

### Phase 7: History + Resume Manager
1. Parse run logs and data/ JSON files
2. Timeline view
3. Resume upload with drag-drop

---

## Technical Notes

- The admin panel does NOT replace the CLI. Both work side by side.
- Profile configs remain Python files — the API reads/writes them.
- CSVs remain the source of truth for job data.
- Form config is a new JSON file (`output/{profile}/form_config.json`).
- Run logs append to `output/{profile}/run_log.json`.
- No authentication needed — this is a local-only tool.
- The Express server proxies to Python scripts, not reimplements them.

---

## File Structure (after build)

```
admin/
├── server.ts          ← Express API (port 5175)
├── src/
│   ├── App.tsx
│   ├── pages/
│   │   ├── SetupWizard.tsx
│   │   ├── JobBoard.tsx
│   │   ├── RunHistory.tsx
│   │   ├── Configuration.tsx
│   │   ├── FormFillConfig.tsx
│   │   └── ResumeManager.tsx
│   ├── components/
│   │   ├── JobTable.tsx
│   │   ├── FilterSidebar.tsx
│   │   ├── ProfileSelector.tsx
│   │   └── ...
│   └── api.ts         ← Typed fetch wrapper
├── package.json
├── vite.config.ts
└── tsconfig.json
```
