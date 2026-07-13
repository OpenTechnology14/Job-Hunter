# Implementation Notes

## 2026-07-12 audit decisions

- Treat local single-user and hosted multi-user operation as different security profiles.
- Preserve the human-in-the-loop rule: automation may navigate and fill, but submission requires explicit user action/confirmation.
- Keep resumes, profiles, credentials, and browser sessions local by default.
- Use deterministic recorded fixtures for required CI; run live provider checks separately because external slugs, schemas, availability, and rate limits change.
- Propose OpenTech as a coordination surface, not as the scraper or browser executor. The local runner owns external navigation and application assistance.

## Verified constraints

- Profile modules are Python and are executed by the loader. They are trusted code, not safe uploads.
- Job state uses CSV read/modify/write and has no demonstrated concurrency protection.
- The admin server uses Flask's debug development server on loopback.
- The test suite can import the active profile and produce user-specific output; isolation is required before public CI.

## Implementation guardrails

1. Never turn a dry-run or generic form-fill completion into a submitted application.
2. Generate a fresh confirmation token immediately before each submission and invalidate it after use/navigation.
3. Use temporary directories and synthetic identities in tests.
4. If hosted mode is retained, replace executable profile modules with declarative validated data.
5. OpenTech payloads must use an allow-list and omit resumes, answers, credentials, local paths, and browser/session data.
