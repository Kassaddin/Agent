---
name: refine
description: Refine an idea or decision on any topic into a complete MVP baseline, or resolve a caller's assigned substantive choices, with a required glossary and recorded agreements and uncertainty.
---

# Refine Ideas

Follow the shared [project layout](../init/references/project-layout.md) for the selected agent area, established host document locations, separate checkpoints, and report destinations. Adoption does not automatically reorganize host content or overwrite entry files.

Own the refinement process, decision rationale, and MVP baseline. For a direct refinement request, develop its first complete MVP baseline. For a caller's handoff, resolve only its assigned choices and return. Apply this to personal, creative, organizational, academic, and technical topics, with depth appropriate to the objective and stakes.

In this skill, **MVP (minimum viable product)** means the smallest coherent version of the intended outcome within the agreed initial scope. The **MVP baseline** is the refined description of that version, including its requirements, decisions, and limits. For a question or decision, the baseline may be a reasoned answer or decision framework. It may be delivered in chat or a discussion record.

## Boundaries and dependencies

Before project-resource access, read and follow the shared [boundary contract](../init/references/boundary-contract.md) and any explicitly selected or layout-discovered boundary file. It governs access, delegation, and actions across this workflow; do not start Init automatically. Missing boundaries allow only existing explicit authorization or work in chat, as the contract describes.

Before refining, read and follow [Glossary](../glossary/SKILL.md), unless already loaded in this context. Establish or locate the topic's glossary and maintain it as meanings become clear. Resolve linked paths relative to this skill's folder. If this required dependency is missing, report the missing path and request its restoration before continuing the dependent workflow. Keep proposed terminology distinct from agreed terminology.

Read and follow [Search](../search/SKILL.md) when source evidence is needed, using the retrieval and delegation rules below. A final document is optional and follows the delivery rules at the end of this skill.

Read the shared [ownership contract](references/ownership-contract.md) when handling a bounded handoff, maintaining a decision record, or resuming work, unless already loaded. The user decides substantive content; Init continues handling access-policy choices.

## Establish the objective and initial scope

Use the existing conversation, designated decision record, and resume checkpoint first, with Context preparation when available under the ownership contract. Identify the intended outcome, relevant context, explicit requirements, constraints, and preferences. For a handoff, retain the caller's assigned scope, settled references, and expected return result. Ask about missing information only when it materially affects that work; do not restart an interview that has already supplied it.

Propose the smallest coherent scope that satisfies the stated objective and required outcomes. Preserve explicit requirements, and ask the user to resolve any proposed removal or material change to them. Define completion criteria appropriate to that scope, using the criteria below as a guide. Adjust them as substantive decisions or new evidence change the scope.

## Work through a dependency graph

Organize unresolved questions as a dependency graph: a question may have several prerequisites. Ask useful questions whose prerequisites are sufficiently established for their answers to be meaningful. A prerequisite remains blocking when its unresolved alternatives would materially change a dependent question or its answer.

Group independent questions into manageable rounds, prioritizing those that could change the direction. A question that depends on an answer still pending in the same round belongs to a later round. After asking a round, follow the boundary contract's whole-task wait until every answer is received or a scoped recommended-answer assumption is authorized. Reassess dependencies after resolution or new evidence; avoid presenting every possible branch at once.

Ask the user to resolve choices that materially affect the objective, scope, priorities, constraints, or substantive trade-offs. Manage question ordering, evidence gathering, and routine workflow choices within established authority. Explain why a question matters when that is unclear. Offer options and a recommendation when useful, with relevant trade-offs and wording that makes disagreement easy. A recommendation or provisional assumption is not an agreed decision.

Probe important assumptions using concrete scenarios, counterexamples, alternative explanations, and consequences. Separate evidence from interpretation. Revisit settled questions when new information materially affects them, and preserve intentional constraints rather than repeatedly arguing against them.

## Find facts and obtain context

Finding and checking facts is your responsibility. Providing necessary personal or situational context is the user's responsibility. Ask focused questions when that context is missing or unclear; do not ask the user to research information retrievable from authorized sources. Context includes circumstances, experiences, intentions, values, preferences, and constraints. Attribute user-provided information appropriately; verify externally checkable claims when they materially affect the outcome and authorized evidence is available.

For factual retrieval, follow Search's preference for one bounded worker and use its direct-lookup fallback only as its contract permits. Let Search govern worker context, effort, budgets, and result format; let the active boundaries govern permissions. If Search is missing or retrieval is blocked, report the specific limitation without inventing evidence or expanding access. A question to the user pauses the entire task; otherwise continue only permitted work.

Treat a pending search as an unresolved prerequisite for its dependent questions. Before any user question, other authorized preparation may continue. Once a question is asked, the shared whole-task wait also gates new searches and processing returned evidence. Consume search results after that gate is satisfied and assess relevance and coverage yourself; results do not establish the user's preferences or decisions.

When a relevant fact remains unavailable, identify it as unknown. Label technical working hypotheses and verify them; they are not user answers. An assumption standing in for a user answer requires explicit permission, selection of the stated recommended option, and the boundary contract's session-end accounting. Otherwise ask and wait. Do not invent user facts, agreement, or access approval.

## Capture deferred topics

Invoking Refine enables [Backlog](../backlog/SKILL.md) capture in this conversation
for the selected project, including later free-form discussion, unless the user
stops capture. Read Backlog when an out-of-scope item arises and pass its meaning,
scope/exclusion evidence, source, and origin. Its explicit dependency hook does
not rely on ambient skill selection or enable other conversations.

Capture clear deferrals automatically within current authority; ask when scope is
unclear. Required prerequisites remain blockers rather than silently deferred
work. Reuse the one project backlog and link its IDs from the topic record where
needed; preserve accepted exclusion reasons there without copying item histories.
Missing Backlog or write restrictions leave entries explicitly unsaved and do not
block otherwise permitted refinement while no user question is pending. Do not activate a service or change host guidance.
When called by Backlog to clarify an item, resolve that assigned choice and return;
do not recapture the same pending candidate recursively.

## Preserve useful state

Track facts and sources, user-provided context, constraints and preferences, agreed decisions and reasons, proposals and assumptions, and open questions distinctly. Keep terminology consistent with the glossary.

For sustained work, a requested record, or a handoff across sessions, maintain the topic's single designated reader-facing decision record under the ownership contract. Reuse a suitable host record; propose the layout contract's topic destination only when one is needed and writing is authorized. Adapt [discussion-template.md](assets/discussion-template.md), keeping useful sections and removing drafting prompts. Capture accepted choices and reasons, reference canonical definitions, and distinguish agreement from pending artifact updates.

Maintain decision entries; the caller maintains the separate resume checkpoint and each artifact owner supplies update and verification status. For a new checkpoint, adapt [checkpoint-template.yaml](assets/checkpoint-template.yaml) and validate its fields against the shared checkpoint schema. Update the relevant sections instead of creating separate per-skill histories. Delivered documents remain faithful representations of this record.

A short discussion may stay in chat. Respect read-only and planning-only requests by keeping proposed updates in the response. Resume from existing records and unresolved questions when available.

## Assess completion and deliver the baseline

For a bounded call, finish when the assigned choices are resolved or their specific blockers are established. Update accepted decisions when permitted and return the decisions, reasons, record references, blockers, and pending artifact updates to the caller. Its workflow remains pending until it resumes; do not run the whole-topic completion or document-delivery path below for that call.

Define and assess completion criteria yourself within the agreed objective and scope. A complete MVP baseline should establish:

- The intended outcome and the context necessary to understand it.
- The complete set of requirements within the MVP scope, relevant constraints, and an explicit distinction between included and deferred work.
- The substantive decisions and their reasons, with consistent terminology and no unresolved contradiction that prevents a coherent baseline.
- How the intended outcome can be assessed, at a level appropriate to the topic.
- Remaining assumptions and unknowns, their effects, and how they can be assessed where needed. Explain why proceeding with them is justified.

An unresolved question blocks completion when it prevents a coherent definition or a justified next step, including a substantive user decision still needed. Record later improvements and assumptions intended for subsequent validation separately. Stop exploring additional branches once the MVP criteria are met. If the user ends the discussion earlier, deliver the partial baseline and identify the unmet criteria.

When the criteria are met, deliver the baseline and explain why it is complete, with meaningful remaining uncertainty. No separate "are we done?" confirmation is required. Preserve the distinction between agreement and recommendation. Completion does not authorize implementing the idea, creating unrelated artifacts, or publishing a document.

Refine establishes the first complete MVP baseline. The planned `iterate` skill will develop that baseline through later feedback and changes; it is not yet available and is not a dependency of Refine. Preserve deferred work for that future step without invoking it.

Continue only into requested delivery. A requested final document uses [To Document](../to-document/SKILL.md); explicit implementation of an agreed small-task baseline uses [Implement](../implement/SKILL.md). These are independent requested outcomes, not a mandatory sequence. Without a delivery request, return the refinement result directly. If a needed skill is unavailable, return the baseline and identify the outstanding request; never treat agreement alone as implementation authority.
