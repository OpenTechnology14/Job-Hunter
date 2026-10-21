---
name: design
description: How to read Job-Hunter's design intent before changing behavior — product scope, locked decisions, release profiles, the supervision and privacy boundaries, and where design docs live.
when_to_use: Use before proposing or building anything that changes product scope, architecture, data flow, storage, the apply flow, hosted/deployed mode, or OpenTech integration. Triggers - "should we add", "redesign", "architecture", "is this in scope", "hosted mode", "add AI matching", "integrate with OpenTech", "rebuild".
---

# Design — Job-Hunter

There was no dedicated design folder before `docs/design/` was created with
`BUILD-PROMPTING-DIGEST.md`. Design intent is spread across the docs below;
read them rather than inferring intent from code.

## Read in this order

1. `AGENTS.md` — non-negotiable boundaries (highest authority).
2. `CONTRIBUTING.md` → "Key Design Decisions".
3. `FUTURE.md` → "Won't Do (By Design)".
4. `docs/IMPLEMENTATION_NOTES.md` — dated decisions + guardrails.
5. `docs/AUDIT.md` / `docs/OPEN_SOURCE_RELEASE_CHECKLIST.md` — release profiles.
6. Relevant proposal in `docs/proposals/` (architecture for OpenTech lives in
   `PROPOSAL_OPENTECH_INTEGRATION_READINESS.md`; safety/test contracts in
   `PROPOSAL_RELEASE_AND_SAFETY_GAP_CLOSURE.md`).
7. `docs/design/BUILD-PROMPTING-DIGEST.md` — how to brief an agent.

## Scope

Local-first, two-phase tool: **(1)** collect + match opportunities into a
spreadsheet; **(2)** assist a *supervised* user with applications. Multi-profile
from one install. The AI-training module finds AI-training *gigs*; the tool
itself does no AI.

## Locked decisions (change only via a proposal + explicit owner sign-off)

| Decision | Source |
|---|---|
| Never submit without fresh, explicit per-job confirmation; dry-run can't submit | `AGENTS.md` 1–2, `FUTURE.md` Won't Do |
| No AI/LLM in core matching; keyword + salary only (AI matching may only ever be optional) | `CONTRIBUTING.md` #1, `FUTURE.md` |
| Filesystem is the database; no DB server requirement | `CONTRIBUTING.md` #2, `FUTURE.md` |
| Per-profile isolation in `output/{name}/` | `CONTRIBUTING.md` #3 |
| Headed (visible) browser automation | `CONTRIBUTING.md` #4 |
| Local CSV default, Google Sheets optional | `CONTRIBUTING.md` #5 |
| CLI first; admin panel is a convenience layer with no build step | `CONTRIBUTING.md` #6 |
| No LinkedIn/Indeed account automation; no paid-board scraping at scale | `FUTURE.md` Won't Do |
| Local-first stays the default; no cloud-only mode | `FUTURE.md` Won't Do |
| Private data stays local; integrations are field-level allow-lists | `AGENTS.md` 3, OpenTech section |
| Profiles are trusted executable code → never accept from untrusted users | `AGENTS.md` 4 |
| OpenTech = coordination surface only; local runner owns scraping + browser | `docs/IMPLEMENTATION_NOTES.md` |

## Release profiles (keep separate)

- **Local single-user:** conditional GO. Supported target.
- **Hosted multi-user (`--deployed`):** NO-GO until auth, authorization, CSRF,
  tenant isolation, upload hardening, atomic persistence, production WSGI land.
  Decision **JH-D01** (keep vs quarantine deployed mode) is open — don't
  resolve it implicitly in a feature PR.

## Reading design intent — method

- Prefer the stated decision over what the code happens to do; if code
  contradicts a locked decision, that's a bug or a proposal, not new intent.
- Any change touching a locked decision, the privacy boundary, or the
  submission path → write a proposal (`docs` skill) first.
- Label claims Verified / Inferred / Proposed / Blocked.
- Unknown? Ask the owner. Don't invent a decision to fill a gap.
