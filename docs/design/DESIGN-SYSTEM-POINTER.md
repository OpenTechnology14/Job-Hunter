# Design system pointer

**Status:** Pointer · **Last reviewed:** 2026-10-23
**Verified against:** hub `Hybrid_Creator_Platform` `main@54266fc` (hub status: drafted, awaiting owner review) ·
Job Hunter `main@2e51dc5`

The ecosystem design-system hub lives at `hybrid-creator-platform/design-system/` (repository
`OpenTechnology14/Hybrid_Creator_Platform`). **The hub is canonical. This file only points
to it and records Job Hunter's local values and overrides.** Token values are never copied
here: two copies drift.

**The hub wins only for tokens marked `approved`.** Today nothing in the hub is approved.
Until a token is approved, Job Hunter keeps its own values (the hub's adoption rule).

> **Public repo, private hub.** Job Hunter is public; the hub is private, so outside readers
> can't open it. This pointer names hub files and states their rules, but it does not
> quote hub content or hub token values.

## 1. Hub files this pointer relies on

| Hub file | What Job Hunter uses it for | Last checked |
|---|---|---|
| `design-system/README.md` | Adoption rule, evidence labels, add-or-reuse and deprecation policy | 2026-10-23 |
| `design-system/tokens.yaml` | Role names to map local variables onto, once approved. The hub records Job Hunter's current admin values as observed at `29df0c9` | 2026-10-23 |
| `design-system/voice-and-tone.md` | The register definitions (§4) | 2026-10-23 |
| `design-system/accessibility.md` | The contrast baseline (§3 finding) | 2026-10-23 |
| `design-system/crosswalk/consumers.md` | Lists Job Hunter as a consumer at this path | 2026-10-23 |
| `design-system/proposals/TEMPLATE.md` | Canonical shape for [`proposals/TEMPLATE.md`](proposals/TEMPLATE.md) | 2026-10-23 |

## 2. What applies here and what doesn't

Job Hunter's only styled output is **one static admin page**, `admin/static/index.html`
(inline CSS and JS, no build step, no templates). It has **no PDF generator** on public
`main`; resumes are user-supplied PDFs. Google Sheets header formatting in
`sheets_sync.py` is a cell background, not a theme.

| Hub category | Applies? | Where / why |
|---|---|---|
| Color tokens | **Yes** | The `:root` custom properties in `admin/static/index.html` |
| Typography | **Yes, family only** | `body` uses the system font stack; there is no type scale |
| Spacing, radius | Partly | Hard-coded `px` values in the admin CSS; no local tokens yet |
| Shadow, motion | Motion only | `transition` rules on hover states; no `box-shadow` is used |
| Accessibility (contrast, focus, keyboard) | **Yes** | The admin page; see §3 |
| Voice and tone | **Yes** | README, `docs/USER_GUIDE.md`, admin UI strings, CLI output |
| Components spec | Rules only | Button, badge and table usage rules can guide the admin HTML. There is no component layer to implement them in |
| Iconography | Partly | The admin and CLI use emoji as status markers, not an icon set |
| Light/dark theming | **Not yet** | The admin is dark-only |
| React / shadcn component conventions | **No** | There is no React layer. "No build step" is a locked decision (`CONTRIBUTING.md`) |
| Generated PDF styling | **No** | There is no generated PDF output |

## 3. Local values and overrides

Local color variables, all in `:root` of `admin/static/index.html`, dark theme only:
`--bg`, `--surface`, `--surface2`, `--border`, `--text`, `--text-dim`, `--accent`,
`--accent-hover`, `--green`, `--red`, `--yellow`, `--orange`. These are Job Hunter's own
values, not hub values. Mapping them to hub role names waits on hub approval.

| Area | Behavior | Rationale | State |
|---|---|---|---|
| Theme | Dark only | Historical; no light theme was ever built | Gap; `JHD-REDESIGN-D01` |
| Font family | System stack | Matches the platform app; no web-font dependency | Kept |
| **Finding:** button text contrast | White on `--accent` is **3.18:1**; on `--accent-hover`, **4.09:1**. Both fail WCAG AA for normal text | None; this is a defect, not an override | Open; fix choice is `JHD-REDESIGN-D07` |

An override without a recorded rationale is a finding. Add a row whenever local CSS
deliberately departs from an approved hub token.

## 4. Register

Job Hunter's user-facing text sits in the **OpenTechnology family register: deep, warm,
measured, narrative.** The owner gave this direction on 2026-10-21. The hub still lists
Job Hunter's register as Blocked; recording it there is `JHD-REDESIGN-D02`.

- **Registers, not names.** No file, prompt, comment or copy in this repo describes
  voice by naming a real person, or as "sounds like" or "in the style of" someone. Use
  descriptors only.
- Documentation stays plain and evidence-first: Verified / Inferred / Proposed / Blocked
  (`docs/README.md`). Copy never claims more than the evidence shows.
- Supervision copy keeps its meaning. Wording around Submit and dry-run may be restyled,
  but never softened in a way that blurs "nothing is submitted without your confirmation."

## 5. Proposals

Design artifacts (mockups, data flows, interaction notes) for Job Hunter start from
[`docs/design/proposals/TEMPLATE.md`](proposals/TEMPLATE.md). Work authorization still
comes from a proposal in `docs/proposals/`. The current design-parity plan is
[`REDESIGN_FROM_OPENTECHAPP_PATTERN.md`](../proposals/REDESIGN_FROM_OPENTECHAPP_PATTERN.md).

A change that adds, changes or deprecates a **hub** token, or changes how more than one
consumer looks, goes in a hub design proposal instead, not here.

## Keeping this current

Re-check this file when the hub revision above is no longer current. A stale revision is
the signal to re-check, not a breakage. When the hub approves a token Job Hunter uses,
update §3 in the same PR that adopts it.
