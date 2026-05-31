# Job Hunter — Known Bugs & Issues

Report bugs via [GitHub Issues](https://github.com/YOUR_USERNAME/job-hunter/issues) or email alexmoody1421@gmail.com.

---

## Open

| # | Severity | Area | Description | Workaround |
|---|----------|------|-------------|------------|
| 1 | Medium | Scraper | Some Greenhouse/Lever company slugs return 404 if the company changes their career page URL | Remove the slug from your profile and re-add the updated one |
| 2 | Low | Resume Gen | Generated 2-page resumes end ~55% down page 2 — bottom half is blank | Add more work experience bullets or use manually created PDFs |
| 3 | Low | Browser Apply | Sites with heavy JavaScript SPAs may not detect form fields correctly | Use `--dry-run` to verify, then apply manually on those sites |
| 4 | Low | Admin Panel | Port 5175 sometimes stays bound after server crash | Run `lsof -ti:5175 \| xargs kill -9` then restart |
| 5 | Low | CSV | Excel may mangle URLs or dates when opening CSV directly | Use "Import" instead of "Open" in Excel, or use Google Sheets |

---

## Fixed

| # | Version | Description | Fix |
|---|---------|-------------|-----|
| — | — | No fixes logged yet | — |

---

## Reporting a Bug

Include:
1. What you did (command, profile name, job source)
2. What you expected
3. What happened instead
4. Error output (terminal text or screenshot)
5. OS and Python version (`python --version`)
