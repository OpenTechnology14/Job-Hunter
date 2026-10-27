"""
Storage Router
Imports push_jobs, pull_ready_jobs, mark_applied, and get_worksheet
from the right backend based on STORAGE_MODE in config.

STORAGE_MODE = "local"  → local CSV at output/{profile}/jobs.csv
STORAGE_MODE = "google" → Google Sheets via service account

All other modules import from here, not directly from the backends.
"""
from config import STORAGE_MODE

if STORAGE_MODE == "google":
    from sheets_sync import push_jobs, pull_ready_jobs, mark_applied, get_worksheet

    def cleanup_stale_jobs(**kwargs):
        """Stale cleanup not yet implemented for Google Sheets mode."""
        return 0
else:
    from local_sync import push_jobs, pull_ready_jobs, mark_applied, get_worksheet, cleanup_stale_jobs
