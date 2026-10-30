# Agent coordination and short idea intake

> **Status:** Direct workflow integration · **Reviewed:** 2026-10-27

Read this guide before planning/assigning work. Reuse an existing authorized coordinator when configured; without runtime setup, facilitate in the current chat and disclose the gap. Application supervision/privacy rules in AGENTS.md retain authority.

## Owner facilitation: ideas, questions, decisions

**Direct source:** [AgentWorkflows](https://github.com/OpenTechnology14/AgentWorkflows) owns reusable procedures and skill/plugin packages. This project's [accepted workflow reference](../.agent-workflows.json) records the exact revision and source hashes; generic instructions are read there rather than maintained as another copy here. Live ideas/questions/decisions stay in the configured private reporting workspace, discovered locally through `~/.t3/agent-module/reporting`. Project product/security rules and canonical work/approval records retain authority.

### Read and check the source

At relevant session start and before advancing a workflow change, resolve the accepted library checkout and run its `scripts/project_reference.py check --library <library-root> --project <actual-project-root> --upstream`. The agent resolves these paths; the owner does not fill them. Read [the reference/update process](https://github.com/OpenTechnology14/AgentWorkflows/blob/07f5d729538491417287bce5a9b98ff9c9f9dc3a/docs/PROJECT_INTEGRATION.md), [startup](https://github.com/OpenTechnology14/AgentWorkflows/blob/07f5d729538491417287bce5a9b98ff9c9f9dc3a/workflows/STARTUP.md), [idea generation](https://github.com/OpenTechnology14/AgentWorkflows/blob/07f5d729538491417287bce5a9b98ff9c9f9dc3a/workflows/IDEA_GENERATION.md), [intake](https://github.com/OpenTechnology14/AgentWorkflows/blob/07f5d729538491417287bce5a9b98ff9c9f9dc3a/workflows/INTAKE.md), [prompt translation](https://github.com/OpenTechnology14/AgentWorkflows/blob/07f5d729538491417287bce5a9b98ff9c9f9dc3a/workflows/PROMPT_TRANSLATION.md) and the current stage directly. The focused GitHub reference workflow checks the same record where this project has Git/CI.

Changed source, different upstream, unavailable network and missing adoption on this branch are explicit gaps, never silent success. A pinned source PR awaiting merge is a release dependency; do not turn that into repeated owner questions. If this branch lacks the reference, the installed manifest's prepared target can provide it while disclosing the unmerged gap. Do not modify a foreign checkout. Update generic behavior in AgentWorkflows first, then regenerate affected project reference/CI files together after review. No new scheduler or coordinator.

### T3 facilitates short ideas

For kickoff, continuing work and decisions, follow [How we work together](https://github.com/OpenTechnology14/AgentWorkflows/blob/07f5d729538491417287bce5a9b98ff9c9f9dc3a/workflows/WORKING_TOGETHER.md): the owner gives short outcome/limits or a plain answer; the agent recovers the checkpoint, fills intake/prompts and returns Changed / Needs your answer / Next.

The existing T3 coordinator helps generate and refine ideas, including bugs and simple changes. **Start and finish with one or two simple sentences and/or a short bulleted list.** The owner can begin with a rough insight; the coordinator reflects it, suggests useful directions and asks only a choice that changes scope. End with the intended outcome, smallest useful version and limits in that same short format.

The agent translates the conclusion into the existing intake requirements: preserve original words and source, classify kind, check evidence/duplicates/parent/PR, record scope and actual authority, then generate the next complete versioned prompt. Technical intake forms and prompt writing are agent work. Keep ideas, pending questions and actual decisions distinct. Bugs use Security/UI, retaining Other/needs-classification; reports and desired changes are not automatically confirmed defects.

**Fallback when the library is unavailable:** keep the short insight → helpful exploration → short conclusion → agent-filled intake → next prompt flow in the current coordinator/canonical record. Preserve holds and unanswered IDs; show at most three real choices. Consider HF fit/availability and bounded effort with capable review. Use existing authorized delivery and distinguish prepared/queued/acknowledged/applied. State persistence or source gaps; an idea conclusion does not itself grant implementation, spend, send or release approval.
