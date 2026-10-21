---
name: docs
description: Documentation discipline for Job-Hunter — which doc owns what, evidence labels (Verified/Inferred/Proposed/Blocked), the proposal queue under docs/proposals/, and README/index conventions.
when_to_use: Use when creating or editing any .md file, writing a proposal, updating README/CLAUDE.md/MAINTENANCE.md after a code change, or adding a doc to docs/. Triggers - "write a proposal", "update the docs", "document this", "README", "add to docs index", "doc drift".
---

# Docs — Job-Hunter

Sources: `docs/README.md` (the index), `docs/PROPOSAL_CREATION_SOP.md`,
`docs/proposals/TEMPLATE_PROPOSAL.md`, `AGENTS.md`, `CONTRIBUTING.md`,
`docs/SUGGESTED_EXISTING_DOC_UPDATES.md`, commit history on `main`.

## Who owns what

| Audience | Docs |
|---|---|
| End user / operator | `README.md`, `SETUP_CHECKLIST.md`, `docs/USER_GUIDE.md`, `docs/ADMIN_PANEL.md`, `HEALTH_CHECK.md`, `DEPLOY.md` |
| Contributor | `CONTRIBUTING.md`, `MAINTENANCE.md` (module-by-module), `APP_PLAYBOOK.md` (single-source reference), `SOURCES.md`, `TESTING.md` |
| Release / audit | `docs/AUDIT.md`, `docs/GAP_AUDIT.md`, `docs/FULL_APPLICATION_AUDIT_MATRIX.md`, `docs/API_ROUTE_AUDIT_LEDGER.md`, `docs/PRESSURE_TEST_LOAD.md`, `docs/OPEN_SOURCE_RELEASE_CHECKLIST.md`, `docs/IMPLEMENTATION_NOTES.md`, `docs/CONTINUOUS_IMPROVEMENT.md` |
| Agents | `AGENTS.md` (cross-tool entry point), `CLAUDE.md`, `.claude/skills/*/SKILL.md`, `docs/design/` |
| Roadmap / bugs | `FUTURE.md` (incl. "Won't Do"), `BUG_TRACKER.md` |

`docs/README.md` is the index. **Any new doc under `docs/` gets a row there.**
The README "Documentation" table lists root docs — add new root docs there.

## Evidence labels (mandatory in audit/proposal/design docs)

**Verified** = directly observed or executed. **Inferred** = follows from code,
not executed. **Proposed** = doesn't exist yet. **Blocked** = verification
unavailable (say why). Record executed evidence separately from inferred or
proposed behavior. Never describe a proposed gate (pytest default, CI) as live.

## Proposal queue

- Location: `docs/proposals/PROPOSAL_<OUTCOME>.md`, from
  `docs/proposals/TEMPLATE_PROPOSAL.md`. Header: Status, Date, Release profile
  (Local single-user / Hosted multi-user / Both), Evidence.
- Required by `docs/PROPOSAL_CREATION_SOP.md` for any *material* change: inventory,
  labels, goals/non-goals, failure paths (missing config, source failure,
  login/CAPTCHA, cancel, retry, duplicate, recovery), a direct injection map
  (file → symbol → before/after → example → verification), security, separate
  deterministic vs live tests, rollout/rollback, open decisions.
- "Incomplete if a developer must guess where a change belongs."
- Link each new proposal from `docs/README.md` → Proposals.
- Status is a free-text line (Draft / Ready … / living doc). There is no formal
  accepted/rejected lifecycle yet — say so rather than invent one.
- Living docs (e.g. the standalone-workflow proposal) are updated as paths are
  run: move a stub checkbox to pass/fail **with a date and what was done**.

## Conventions observed in history

- **Add-only doc updates** when shipping features: extend sections, don't
  delete content others rely on (see commit messages on `main`).
- A feature PR updates every doc that names the affected surface — typically
  README features + file tree + flags, `CLAUDE.md`, `MAINTENANCE.md`,
  `TESTING.md` (new numbered scenario table), `SOURCES.md`, `FUTURE.md`
  "Recently Shipped".
- Commands in docs use placeholder profiles (`yourname`, `<p>`, `Example`).
  **No real names, emails, phones, cities, or employers** in any tracked file.
- Don't hardcode test counts (known drift: docs said 24, inventory was 27).
- Known pending corrections live in `docs/SUGGESTED_EXISTING_DOC_UPDATES.md`;
  when you fix one, remove it from that file in the same PR.

## Cross-tool rule

Skills are written once in `.claude/skills/<name>/SKILL.md`. Claude Code loads
them natively; Codex/ChatGPT and other agents reach them through the `AGENTS.md`
§Skills pointer. Don't fork copies per tool — edit the SKILL.md.
