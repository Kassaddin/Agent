---
name: backlog
description: Capture, deduplicate, and clarify out-of-scope topics in one project backlog when Backlog or direct or whole-topic Refine enables capture for the conversation.
---

# Backlog

Own the project's captured backlog entries and their consistency. Preserve topics, functional parts, dependencies, and potential work for later consideration without changing the current baseline or committing the user to do them.

## Activate within the conversation

Invoke Backlog or start direct or whole-topic [Refine](../refine/SKILL.md) to enable capture for the selected project in this conversation. A bounded assigned-choice Refine handoff can use the explicit capture hook only while capture is already active. Once enabled, capture may continue during free-form discussion until the user stops it. Do not enable capture from unrelated conversation content, an existing backlog file, project adoption, or another conversation. Do not create a background service or persistent activation flag. Reestablish the project and its canonical destination when the conversation changes project.

Read the shared [boundary contract](../init/references/boundary-contract.md), selected policy, [layout contract](../init/references/project-layout.md), and [ownership contract](../refine/references/ownership-contract.md). Invocation does not add permissions. Caller restrictions still apply: a read-only audit/search, no-file request, or planning-only write limit cannot be bypassed through Backlog. Return unsaved entries when writing is not authorized or is blocked; never report them as saved. Init owns access-policy changes.

## Locate the one project backlog

Reuse the user-selected file or the host's designated backlog. Use existing guidance or Project Context mappings first; [Search](../search/SKILL.md) can locate missing references within authorized sources. Inspect plausible known locations, not unrelated projects or a whole-project history. Multiple plausible backlogs require selection rather than a freshness or permissiveness guess.

Otherwise use `docs/backlog.md` in the host's established reader area; without a suitable host location, propose the selected kit's `docs/backlog.md` fallback. State the destination before its first write. Create the file and folders only when an actual item needs capture. Preserve an existing compatible format instead of migrating it. Keep one file per project, not one per topic, skill, or conversation. Use [Glossary](../glossary/SKILL.md) for established meanings and retain terminology agreement status.

## Decide what belongs

- Capture clearly out-of-scope items automatically, including agent-identified items. Their relevance and exclusion must be supported by the current discussion objective, baseline, or user deferral. Do not invent items to populate the backlog or scan past conversations automatically.
- If it is unclear whether an item belongs to the current work, ask the user. Keep the candidate unsaved and pause the whole task until the answer is received or a recommended-answer assumption is explicitly authorized under the boundary contract. Do not silently move an agreed requirement out of scope.
- A dependency needed for the current outcome remains a blocker in the active workflow. A linked future-work entry can coexist when useful, but capture cannot resolve, hide, or defer that prerequisite by itself.
- Recording an item is not agreement to its substance, a priority, an estimate, a deadline, or implementation authorization. Preserve whether it came from the user or the agent.

## Capture, deduplicate, and clarify

Inspect relevant existing entries before adding one. Equivalent meaning and scope justify enriching an existing item; matching titles alone do not. Retain its ID and useful source references. If a merge could erase a legitimate distinction, ask before merging; related but different items may remain separate with a link.

For a new item, assign a stable unique ID such as `BL-001`; continue the existing scheme, and never renumber items or reuse an occupied ID. Preserve a concise title and description, why it is outside the originating scope, a verifiable source reference, and user/agent origin. Add related references only when useful. [The template](assets/backlog-template.md) provides a new-file format, not a mandate to rewrite an existing backlog.

A source can be a verified file/decision link or an identifiable conversation description with its date/topic and enough context for later retrieval. Do not fabricate chat URLs, source quotations, or exact locators. Clarify only enough to preserve the intended item; an unclear substantive meaning uses a bounded Refine choice, not an unsolicited refinement of the deferred topic.

Notify queued file changes as current policy requires; no repeated capture approval is needed for clear items when existing authority permits writing. Batch related updates where practical. Recheck the file before writing and preserve concurrent edits. Verify the saved content, IDs, source links, and absence of unintended duplicate entries.

## Return to the caller

Return added/updated IDs, the canonical file, unresolved questions, and actual saved/unsaved status briefly, then resume the originating workflow. No captured item needs a separate interview or deliverable. Repeated equivalent input needs no write unless it adds useful context or provenance.

This MVP captures, deduplicates, and clarifies only. It does not assign priorities, schedule work, manage lifecycle/status, remove old entries, or launch implementation. Accepted choices and reasons remain in their topic record; blockers and execution state remain in the caller's existing record/checkpoint. Link those sources rather than copying their histories. Captured future work may be taken up through a later explicit request; Backlog does not perform that transition itself.
