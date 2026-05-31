# User Guide — Job Hunter

Simple usage guide for non-technical users. No coding required after initial
setup is complete.

---

## What This Does

Job Hunter automatically searches 17 job boards for jobs matching your skills,
salary range, and location. It saves results to spreadsheet files you review
in Excel or Numbers. You mark the ones you want, and the system applies for you.

---

## Option A: Use the Admin Panel (Recommended)

The admin panel is a web dashboard that replaces manual CSV editing.

### Start it:
```bash
cd ~/Downloads/job-hunter && source venv/bin/activate
python admin/server.py
```

Then open **http://localhost:5175** in your browser.

### What you can do:
- **Dashboard** — see job counts, run scrapes with one click
- **Jobs** — browse, search, filter, and approve/reject jobs by clicking Y/N
- **Resumes** — view all your resume PDFs
- **Form Fill** — configure auto-fill answers for job applications
- **Setup** — check that everything is configured correctly

### Daily workflow with admin panel:
1. Open http://localhost:5175
2. Click "Run API Scrape" on the Dashboard
3. Go to Jobs tab, review new jobs, click Y for ones you want
4. Run auto-apply from Terminal (see Step 4 below)

---

## Option B: Use Terminal + Spreadsheet

### Step 1: Run the scrape

Open Terminal, paste these two lines:

```bash
cd ~/Downloads/job-hunter && source venv/bin/activate
python run_scrape.py --profile yourname
```

Wait 1-3 minutes. It will print how many jobs it found.

### Step 2: Review jobs

Open your job list:
```bash
open output/yourname/jobs.csv
```

This opens in Excel or Numbers. You'll see columns:
- **Job Title** — the position
- **Company** — who's hiring
- **Location** — where
- **Work Type** — Remote, On-site, or Hybrid
- **Salary** — if listed
- **Apply** — **this is where you say yes or no**

### Step 3: Approve jobs

For each job you want to apply to:
1. Put **Y** in the Apply column
2. Put **N** to skip (or leave blank)
3. Save the file

### Step 4: Auto-apply

```bash
python run_apply.py --profile yourname --dry-run
```

This opens a browser and fills out applications for your approved jobs.
The `--dry-run` flag means it won't actually submit — just shows you what
it would do. When you're ready for real:

```bash
python run_apply.py --profile yourname
```

It pauses before every submission so you can review.

---

## LinkedIn & Indeed Jobs

These are scraped separately and saved to a different file:

```bash
python run_scrape_browsers.py --profile yourname
open output/yourname/browser_jobs.csv
```

This CSV has extra columns:
- **Easy Apply** — Yes means one-click apply is available
- **Direct Apply Link** — a link that goes straight to the application

**These jobs do NOT auto-apply.** To apply:

### Option A: Manual
Click the Job URL, apply on the website yourself.

### Option B: Claude Chrome Extension (recommended)
1. Install the Claude in Chrome extension
2. Open a job URL from the CSV in Chrome
3. The extension can help fill forms and submit for you
4. Mark approved jobs with **Y** in the Apply column so you know which to do

---

## What Each File Is

| File | What's in it |
|------|-------------|
| `output/yourname/jobs.csv` | Jobs from API sources — auto-apply works here |
| `output/yourname/browser_jobs.csv` | LinkedIn/Indeed jobs — manual apply only |
| `output/yourname/form_config.json` | Custom form fill answers (salary expectations, etc.) |
| `output/yourname/resumes/` | Your resume PDFs (one per role) |

---

## How Auto-Apply Works

When you run `run_apply.py`, it:

1. Reads your CSV for jobs marked **Y**
2. Opens a visible Chrome browser (you can watch)
3. For each job:
   - Goes to the application page
   - Picks the right resume based on job category
   - Fills in your name, email, phone, etc.
   - Uploads your resume PDF
   - **Pauses and asks you** before clicking Submit
4. After you confirm, it submits and marks the job as "Done"

**It never submits without asking you first.**

### What it fills automatically:
- Name, email, phone
- City, state, country
- Current company and title
- Years of experience
- LinkedIn and portfolio URLs
- Custom answers you configure (see below)

### What you fill manually:
- Cover letters (unless you add a default)
- Specific questions about the role
- Anything the system doesn't recognize

---

## Custom Form Answers

Some applications ask extra questions like:
- "What are your salary expectations?"
- "Are you willing to relocate?"
- "Do you require visa sponsorship?"

You can pre-configure answers. Edit `output/yourname/form_config.json`:

```json
{
  "custom_fields": [
    {"pattern": "salary.?expect", "value": "Negotiable"},
    {"pattern": "relocat", "value": "No"},
    {"pattern": "sponsor", "value": "N/A - US Citizen"},
    {"pattern": "earliest.?start", "value": "Immediately"},
    {"pattern": "how.?hear", "value": "Online job search"}
  ],
  "select_defaults": [
    {"pattern": "gender", "value": "Prefer not to say"},
    {"pattern": "race|ethnicity", "value": "Prefer not to say"},
    {"pattern": "veteran", "value": "No"},
    {"pattern": "disability", "value": "Prefer not to say"},
    {"pattern": "work.?auth", "value": "Yes"}
  ]
}
```

The "pattern" is matched against form labels. When the system sees a form
field whose label contains that pattern, it fills in the value automatically.

---

## Changing Location

If you move or want to search a different area:

1. Open `profiles/yourname.py`
2. Find the `LOCATION_FILTER` section
3. Change `city`, `state`, and `nearby_cities`
4. Also update `SEARCH_SETTINGS["locations"]`
5. Delete your old CSV: `rm output/yourname/jobs.csv`
6. Run a fresh scrape

---

## Common Questions

**Q: Will it apply without asking me?**
No. It always pauses before submitting. In dry-run mode it doesn't submit at all.

**Q: Can I use it for multiple people?**
Yes. Each person has their own profile, resumes, and CSV files.
Just use `--profile theirname` on every command.

**Q: What if a job board is down?**
The scraper skips it and continues with the others. You'll see 0 results
for that source in the output.

**Q: How do I add more job boards?**
See SOURCES.md for the full list and setup instructions.

**Q: Can I run it automatically every day?**
Yes. Set up a cron job (Mac/Linux):
```bash
crontab -e
# Add this line (runs at 8am and 8pm):
0 8,20 * * * cd ~/Downloads/job-hunter && ~/Downloads/job-hunter/venv/bin/python run_scrape.py --profile yourname
```

**Q: How do I update my resume?**
Replace the PDF file in `output/yourname/resumes/` with the same filename.
Or update the filename in your profile and drop the new PDF in.
