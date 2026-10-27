# Proposal Creation SOP

Proposals must be grounded in observed code and executable evidence.

1. Inventory the relevant files, routes, entry points, tests, local data, and external services.
2. Label statements Verified, Inferred, Proposed, or Blocked.
3. State goals, non-goals, local/hosted release profile, privacy boundary, and supervision boundary.
4. Trace first run, normal success, missing configuration, source failure, login/CAPTCHA, cancellation, retry, duplicate, and recovery paths.
5. Give direct injection locations: file, function/route/component, before/after behavior, example payload/config/UI copy, and verification.
6. Cover authentication, CSRF, tenant ownership, path safety, executable profiles, resume/form data, rate limits, and logs.
7. Specify deterministic tests separately from live provider smoke tests.
8. Include rollout, rollback, documentation changes, unresolved decisions, and release gates.
9. Every open decision gets a stable ID (`JH-D0N`, or a proposal-scoped prefix such as `JHD-REDESIGN-D0N`) and ends with a one-sentence plain-English **Question:** with two or three choices and a marked recommendation plus its tradeoff. The full explanation stays beside it. Record answers under the same ID. Open repo-wide decisions are listed in `docs/GAP_AUDIT.md` → Open decisions.

Use [the proposal template](proposals/TEMPLATE_PROPOSAL.md). A proposal is incomplete if a developer must guess where a change belongs or how failure/recovery behaves.
