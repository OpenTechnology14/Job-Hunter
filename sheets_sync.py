"""
Google Sheets Sync
Push scraped jobs TO the sheet. Pull "Ready to Apply" jobs FROM the sheet.

Usage:
    from sheets_sync import push_jobs, pull_ready_jobs
"""
import json
from datetime import datetime, timedelta
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from config import (
    GOOGLE_CREDS_PATH, GOOGLE_SHEET_ID, GOOGLE_SHEET_NAME,
    SHEET_COLUMNS, DATA_DIR,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client():
    creds = Credentials.from_service_account_file(GOOGLE_CREDS_PATH, scopes=SCOPES)
    return gspread.authorize(creds)


def get_worksheet(client=None):
    if client is None:
        client = get_client()
    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)

    try:
        ws = spreadsheet.worksheet(GOOGLE_SHEET_NAME)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(
            title=GOOGLE_SHEET_NAME, rows=500, cols=len(SHEET_COLUMNS)
        )

    existing = ws.row_values(1)
    if not existing or existing != SHEET_COLUMNS:
        ws.update("A1", [SHEET_COLUMNS])
        ws.format("A1:N1", {
            "backgroundColor": {"red": 0.1, "green": 0.1, "blue": 0.1},
            "textFormat": {
                "foregroundColor": {"red": 1, "green": 1, "blue": 1},
                "bold": True, "fontSize": 11,
            },
            "horizontalAlignment": "CENTER",
        })
        ws.freeze(rows=1)

    return ws


def get_existing_urls(ws) -> set:
    try:
        urls = ws.col_values(10)  # Column J = URL
        return set(urls[1:])
    except Exception:
        return set()


def push_jobs(jobs: list[dict], ws=None):
    """Push matched jobs to the Google Sheet. Skips duplicates by URL."""
    if ws is None:
        ws = get_worksheet()

    existing = get_existing_urls(ws)
    today = datetime.now().strftime("%Y-%m-%d")

    new_rows = []
    for job in jobs:
        url = job.get("url", "")
        if url in existing:
            continue

        # Normalize date_posted for sheets
        date_posted = ""
        raw_dp = job.get("date_posted", "")
        if raw_dp:
            try:
                if isinstance(raw_dp, (int, float)):
                    date_posted = datetime.fromtimestamp(raw_dp).strftime("%Y-%m-%d")
                elif str(raw_dp).isdigit():
                    date_posted = datetime.fromtimestamp(int(raw_dp)).strftime("%Y-%m-%d")
                elif "T" in str(raw_dp):
                    date_posted = datetime.fromisoformat(str(raw_dp).replace("Z", "+00:00")).strftime("%Y-%m-%d")
                else:
                    date_posted = str(raw_dp)[:10]
            except (ValueError, OSError):
                date_posted = str(raw_dp)[:10] if raw_dp else ""

        row = [
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", ""),
            job.get("salary", ""),
            job.get("role_category_label", "Unmatched"),
            job.get("match_reason", ""),
            job.get("apply_method", "✍️ Manual"),
            job.get("status", "🔍 New"),
            job.get("recommended_resume", ""),
            url,
            job.get("source", ""),
            date_posted,
            today,
            "",   # Date Applied
            "",   # Notes
        ]
        new_rows.append(row)

    if not new_rows:
        print("  No new jobs to add.")
        return

    next_row = len(ws.col_values(1)) + 1
    ws.update(f"A{next_row}", new_rows)

    # Color-code by role category
    try:
        from gspread_formatting import CellFormat, Color, format_cell_range

        for i, row in enumerate(new_rows):
            row_num = next_row + i
            status = row[7]
            if "New" in status:
                bg = Color(1.0, 1.0, 0.88)     # Light yellow
            elif "Ready" in status:
                bg = Color(0.85, 0.95, 0.85)   # Light green
            else:
                bg = Color(1, 1, 1)
            format_cell_range(ws, f"A{row_num}:N{row_num}", CellFormat(backgroundColor=bg))
    except ImportError:
        pass

    print(f"  ✅ Added {len(new_rows)} jobs to sheet")

    # Apply method breakdown
    methods = {}
    for row in new_rows:
        m = row[6]
        methods[m] = methods.get(m, 0) + 1
    for method, count in sorted(methods.items(), key=lambda x: x[1], reverse=True):
        print(f"    {method}: {count}")


def pull_ready_jobs(ws=None) -> list[dict]:
    """Pull jobs marked '✅ Ready to Apply' from the sheet."""
    if ws is None:
        ws = get_worksheet()

    all_rows = ws.get_all_records()
    ready = []

    for i, row in enumerate(all_rows):
        status = str(row.get("Status", ""))
        if "Ready" in status or "ready" in status.lower():
            ready.append({
                "sheet_row": i + 2,  # +2 for header + 0-index
                "title": row.get("Job Title", ""),
                "company": row.get("Company", ""),
                "location": row.get("Location", ""),
                "salary": row.get("Salary", ""),
                "role_category_label": row.get("Role Category", ""),
                "apply_method": row.get("Apply Method", ""),
                "recommended_resume": row.get("Resume Version", ""),
                "url": row.get("URL", ""),
                "source": row.get("Source", ""),
            })

    print(f"  📋 {len(ready)} jobs marked 'Ready to Apply'")
    return ready


def mark_applied(ws, sheet_row: int, resume_used: str = ""):
    """Update a row's status to Applied with today's date."""
    today = datetime.now().strftime("%Y-%m-%d")
    ws.update_cell(sheet_row, 8, "✅ Applied")         # Status column (H)
    ws.update_cell(sheet_row, 13, today)                # Date Applied column (M)
    if resume_used:
        ws.update_cell(sheet_row, 9, resume_used)       # Resume Version column (I)


def sync_scraped_to_sheet(input_file: str = None):
    """Load matched jobs from JSON and push to sheet."""
    if input_file:
        job_file = Path(input_file)
    else:
        files = sorted(DATA_DIR.glob("matched_jobs_*.json"), reverse=True)
        if not files:
            files = sorted(DATA_DIR.glob("raw_jobs_*.json"), reverse=True)
        if not files:
            print("No job files found. Run scraper first.")
            return
        job_file = files[0]

    print(f"  Loading: {job_file}")
    with open(job_file) as f:
        jobs = json.load(f)

    push_jobs(jobs)
    print(f"\n  🔗 Sheet: https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}")


if __name__ == "__main__":
    sync_scraped_to_sheet()
