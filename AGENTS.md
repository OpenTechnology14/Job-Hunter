# AGENTS.md — Job-Hunter

Read this file before modifying the repository.

## Project identity

Job-Hunter is a local-first, two-phase job-search tool: it collects/matches opportunities, then assists a supervised user with application preparation. The default security profile is one trusted user on one local machine.

## Non-negotiable boundaries

1. Never submit an application without a fresh, explicit user confirmation for that exact job/page state.
2. Dry-run mode must be structurally unable to call a submit primitive.
3. Profiles, resumes, form answers, credentials, browser sessions, and history stay local unless the user explicitly enables a documented, field-level integration.
4. Treat profile `.py` files as trusted executable code. Do not accept them from untrusted hosted users.
5. Do not present the Flask admin server as hosted/multi-user-ready without application auth, authorization, CSRF, tenant isolation, hardened uploads, safe persistence, and a production WSGI path.
6. External job sources are unstable. Required CI uses deterministic fixtures; live checks are separate smoke tests.

## Repository guidance

- `README.md`, `SETUP_CHECKLIST.md`, and `docs/USER_GUIDE.md` describe user workflows.
- `TESTING.md` and `run_tests.py` define verification.
- `SECURITY.md` and `docs/OPEN_SOURCE_RELEASE_CHECKLIST.md` define release constraints.
- `docs/AUDIT.md` and `docs/GAP_AUDIT.md` record current evidence and gaps.
- Material proposals must follow `docs/PROPOSAL_CREATION_SOP.md` and `docs/proposals/TEMPLATE_PROPOSAL.md`.

## Skills

Task-specific rules live in `.claude/skills/<name>/SKILL.md` — **one source, two readers**:

- **Claude Code** auto-discovers and loads these skills from their frontmatter (`name`, `description`, `when_to_use`).
- **Codex, ChatGPT, and other agents** don't load skills natively: read the matching SKILL.md below as plain markdown before starting that kind of task.

| Skill | Read before |
|---|---|
| [`code-creation`](.claude/skills/code-creation/SKILL.md) | Writing features, sources, fixes, admin routes, tests |
| [`docs`](.claude/skills/docs/SKILL.md) | Editing any `.md`, writing proposals, updating README/indexes |
| [`design`](.claude/skills/design/SKILL.md) | Changing scope, architecture, apply flow, hosted mode, integrations |
| [`audits`](.claude/skills/audits/SKILL.md) | Audits, readiness checks, gap ledger updates, PR triage |

Edit the SKILL.md itself; never fork per-tool copies. If a skill conflicts with this file, this file wins.

## Design

Design docs live in `docs/design/`. Start with [`docs/design/BUILD-PROMPTING-DIGEST.md`](docs/design/BUILD-PROMPTING-DIGEST.md) — how to brief an agent to extend or rebuild Job-Hunter. Locked decisions are summarized in the `design` skill.

## Coding and test rules

- Use synthetic identities and temporary directories in tests; never load the operator's active profile.
- Add regression tests for fixes and exercise production functions rather than duplicating their logic in tests.
- Keep secrets and personal/output files ignored. Update examples with placeholders only.
- Validate all profile names, filenames, URLs, uploaded files, and external payloads at trust boundaries.
- Use atomic/concurrency-safe persistence for paths touched by background scraping and UI mutations.
- Document executed evidence separately from inferred or proposed behavior.

## OpenTech integration

OpenTech may coordinate sanitized queue/status metadata. The local runner remains responsible for scraping and supervised browser actions. Do not send resumes, answers, credentials, cookies, local paths, or personal profile details. Integration must be optional, idempotent, bounded during outages, and unable to weaken the submission-confirmation rule.
