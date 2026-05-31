# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest on `main` | Yes |
| Older commits | No |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT open a public issue.** Security bugs disclosed publicly put all users at risk.
2. Email **alexmoody1421@gmail.com** with:
   - Description of the vulnerability
   - Steps to reproduce
   - Impact assessment
   - Suggested fix (if any)
3. You will receive a response within **72 hours** acknowledging receipt.
4. A fix will be developed and released within **14 days** for critical issues.

## Scope

The following are in scope:
- API scraper modules (`scraper.py`, `scraper_extended.py`)
- Browser automation (`browser_apply.py`, `run_scrape_browsers.py`)
- Admin panel server (`admin/server.py`)
- Profile loader (`config.py`) - especially the `exec()` call
- Form auto-fill (`form_config_example.json` patterns)
- Local file read/write operations

The following are out of scope:
- Third-party job board APIs themselves
- Google Sheets API / Google OAuth
- Playwright browser engine vulnerabilities

## Known Security Considerations

- **`admin/server.py` binds to `127.0.0.1` only.** Do not change this to `0.0.0.0` in production without adding authentication.
- **Profile loading uses `exec()`.** Profile `.py` files are executed as Python code. Only load profiles you trust.
- **No authentication on admin panel.** The admin panel is designed for localhost use only. If deploying remotely, add authentication middleware.
- **CSV files contain job data, not credentials.** But they may contain personal info (name, email, phone) from profile config.
- **`.env` file is gitignored.** API keys should never be committed.

## Disclosure Policy

After a fix is released, the vulnerability will be disclosed publicly in the release notes. Credit will be given to the reporter unless they request anonymity.
