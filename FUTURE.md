# Job Hunter — Roadmap

Planned features and improvements. No promises on timelines.

---

## Next Up

### Authentication for Admin Panel
- Add basic auth (username/password) to the Flask admin panel
- Required before deploying on a public server
- Currently safe only on localhost

### More Job Board Sources
- Wellfound (AngelList) — startup jobs
- The Muse — company profiles + jobs
- Adzuna — aggregator with free API tier
- Workday — enterprise career pages (common ATS)
- Google Jobs via SerpAPI (paid, ~$100/mo)

### Browser Scraping Improvements
- LinkedIn Easy Apply detection and auto-fill
- Indeed direct apply support
- Handle multi-page application flows
- Better CAPTCHA detection (pause and alert user)

---

## Medium Term

### AI-Powered Matching (Optional)
- LLM-based job description analysis
- Resume-to-job fit scoring
- Auto-generate cover letters per job
- Keep as optional — core matching stays keyword + salary

### Notification System
- Email alerts for new high-match jobs
- Daily/weekly digest of new results
- Configurable per profile

### Application Tracking
- Track application status beyond "Done" (Applied, Phone Screen, Interview, Offer, Rejected)
- Timeline view of application history
- Notes per application stage

### Resume Customization
- Generate tailored resumes per job posting
- Highlight relevant skills based on job description
- Multiple resume templates (not just Helvetica 2-page)

---

## Long Term

### Web Dashboard
- Replace Flask admin panel with a proper web app
- Real-time job feed updates
- Collaborative features for career coaches managing multiple clients

### API Layer
- RESTful API for third-party integrations
- Webhook support for new job notifications
- Integration with calendar apps for interview scheduling

### Analytics
- Job market trends by role/location
- Salary distribution charts
- Application success rate tracking
- Source quality comparison (which boards yield interviews)

### Mobile Support
- Progressive web app for reviewing jobs on mobile
- Push notifications for new matches
- Quick approve/reject from phone

---

## Won't Do (By Design)

- **Paid job board scraping at scale** — legal risk, not worth it
- **LinkedIn/Indeed account automation** — violates ToS, accounts get banned
- **Fully autonomous applying** — always pause for human review before submit
- **Cloud-only mode** — local-first stays the default
- **Database server requirement** — filesystem stays the primary store
