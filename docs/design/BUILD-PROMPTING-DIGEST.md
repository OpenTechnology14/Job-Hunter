# Build Prompting Digest

**Status:** Living design doc
**Date:** 2026-10-21
**Release profile:** Local single-user
**Evidence:** Distilled from `README.md`, `CLAUDE.md`, `AGENTS.md`,
`CONTRIBUTING.md`, `MAINTENANCE.md`, and AI-co-authored commit messages on
`main`. No separate AI build logs exist in the repo — the commit bodies are
the build record (**Verified**: commits `1c52ee7`, `b240cee` and earlier carry
`Co-Authored-By: Claude` trailers).

How to prompt a coding agent (Claude Code, Codex, ChatGPT, …) to extend or
rebuild Job-Hunter without breaking what's already decided.

---

## 1. What the agent must load first

| Order | File | Why |
|---|---|---|
| 1 | `AGENTS.md` | Non-negotiable boundaries; pointers to skills + this doc |
| 2 | `CLAUDE.md` | Full structure, setup walk-through, daily usage, flags |
| 3 | Relevant skill in `.claude/skills/` | `code-creation`, `docs`, `design`, `audits` |
| 4 | `MAINTENANCE.md` section for the module touched | Module internals and known issues |
| 5 | `docs/GAP_AUDIT.md` | So the agent doesn't "fix" something into a known gap |

Claude Code loads skills automatically; for other tools, say "read `AGENTS.md`
and follow its §Skills pointers" in the first prompt.

## 2. Context to put in every build prompt

The system in one paragraph (paste-ready):

> Job-Hunter is a local-first, two-phase Python tool. Phase 1 scrapes free job
> APIs/web/X-Ray/gig boards, matches by keyword + salary (no AI), runs quality
> filters, and writes `output/{profile}/jobs.csv` (or a Google Sheet). Phase 2
> reads rows the user marked `Y`, opens a visible Playwright browser, picks the
> resume per role, fills the form, and **pauses for explicit confirmation before
> every submit**; `--dry-run` never submits. Profiles are trusted Python data
> files. A Flask admin panel (`localhost:5175`, single HTML file, no build step)
> is optional. Filesystem is the database.

Then state the boundaries the agent must not cross (from `AGENTS.md`):
submission confirmation, dry-run can't submit, private data stays local,
profiles are trusted code, don't claim hosted readiness, no AI in core matching.

## 3. Prompt shape that has worked

From the commit history, successful feature passes shared this shape:

1. **One outcome per prompt**, named as a feature ("Boolean & Google X-Ray
   search", "result quality filters", "screener-question guard").
2. **Where it plugs in** — module, `run_scrape.py` step, profile key, CLI flag,
   admin page/route. Example: *"wire as run_scrape Step 1e with `--xray/--no-xray`,
   default `boolean_search: False` in config, expose strings on the admin Config page."*
3. **Degradation behavior** — what happens when the source throttles or is
   down ("retry once, degrade to 0 with a clear note"). Sources must fail soft.
4. **Opt-in + toggles** — new behavior defaults off or is togglable via
   `SEARCH_SETTINGS` and the admin Config page; old profiles keep working.
5. **Docs list, add-only** — name every doc to update (README features + tree +
   flags, `CLAUDE.md`, `MAINTENANCE.md`, `SOURCES.md`, `TESTING.md` new section,
   `FUTURE.md` Recently Shipped, `docs/USER_GUIDE.md`).
6. **Verification** — the exact command(s) and, for apply-path changes, a
   supervised `--dry-run` against a real form.

Template:

```text
Read AGENTS.md and follow its §Skills (code-creation + docs).
Goal: <one feature>.
Plug-in points: <module>, <run_scrape step / entry point>, <profile key + default>,
<CLI flag>, <admin page/route if any>.
Failure behavior: <throttle/down/missing key → what the user sees>.
Constraints: no AI in matching; dry-run never submits; no PII in tracked files;
admin panel stays a single HTML file.
Tests: regression test calling the production function, synthetic profile + temp
dir; run `python run_tests.py --<category>` and paste output.
Docs (add-only): <list>.
Branch <name>, PR using the template.
```

## 4. Prompts for common extensions

| Task | Key instructions to include |
|---|---|
| New job source | Standard job dict keys; return `[]` on error; `time.sleep` between pages; respect ToS; add to `SOURCES.md` + README table |
| New matching / filter rule | Exercise `matcher.match_jobs` / `quality_filter` directly in tests; saved-search `🔎` rows stay exempt; Y/Done rows never removed |
| Auto-fill change | Never weaken `_is_screener_question()`; identity data never lands in free-text/EEO questions; verify with dry-run on a live form |
| Admin route | Add to `MAINTENANCE.md` table and `docs/API_ROUTE_AUDIT_LEDGER.md`; validate profile name/filename; no build step |
| Audit / readiness | Use `audits` skill; separate local vs hosted verdicts; only executed evidence is Verified |
| Material/architectural change | Proposal first per `docs/PROPOSAL_CREATION_SOP.md`; don't implement in the same prompt |

## 5. Prompting a full rebuild

If rebuilding from scratch, prompt in phases and verify each before moving on:

1. **Skeleton** — `config.py` profile loader + `profiles/example_profile.py`
   (`USER_PROFILE`, `ROLE_PROFILES`, `SEARCH_SETTINGS`, `LOCATION_FILTER`,
   `STORAGE_MODE`), `storage.py` → `local_sync.py` with `SHEET_COLUMNS`.
2. **One source end-to-end** — e.g. Greenhouse → matcher → CSV. Verify dedupe.
3. **Remaining sources** one prompt each; then web search, X-Ray, gig modules.
4. **Quality filters** with config toggles + retro-clean CLI.
5. **Apply path** — `resume_picker.py`, `browser_apply.py`, `run_apply.py`
   with dry-run and the confirmation gate built *first*, then form filling.
6. **Admin panel** — Flask + single HTML file; local mode only first.
7. **Tests + CI** — deterministic offline suite as the gate; live smoke separate.

Tell the agent which `docs/GAP_AUDIT.md` items to close during the rebuild
(e.g. atomic CSV writes, synthetic test profile) rather than re-creating them.

## 6. Anti-patterns to forbid in prompts

- "Just make it submit automatically" — violates the locked supervision rule.
- "Add an LLM to rank jobs" without "optional, off by default, core stays
  deterministic".
- "Deploy it for multiple users" — hosted mode is NO-GO (decision JH-D01 open).
- Pasting a real profile, resume, or `.env` into the prompt or a test fixture.
- Asking for a doc rewrite that deletes sections — updates are add-only.
- Reporting "CI green" without reading the actual `CI / offline-tests` result (it is not a required check yet; JH-D05).

## 7. Keeping this doc current

Update when a new pattern lands (a new plug-in point, a new gate, a closed gap
that changes what agents must do). Record changes in the commit body, as the
existing history does.
