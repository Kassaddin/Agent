---
name: to-document
description: Synthesize a Refine baseline, conversation, notes, or supplied material into a complete document, using Glossary and resolving every substantive gap before drafting, with unresolved substantive user choices handled through Refine.
---

# To Document

Create a faithful synthesis of the supplied material for its intended reader. Accept a Refine baseline, standalone conversations, notes, or other supplied material. Suitable outputs include proposals, plans, briefs, specifications, essays, and other documents on any topic.

Own document composition, faithful representation, and delivery completeness. Use the shared [ownership contract](../refine/references/ownership-contract.md) for handoffs, the designated decision record, and resume checkpoints; load it only when those operations are needed. As a caller, retain the surrounding request and continuation.

The MVP is minimal yet full: the smallest coherent version of the intended outcome, with complete coverage of the agreed scope and requirements. Use only necessary detail and preserve every required point.

**Substantive gap:** Missing, conflicting, or ambiguous information necessary to establish the document's meaning, required coverage, or conclusions.

## Boundaries and dependencies

Before project-resource access, read and follow the shared [boundary contract](../init/references/boundary-contract.md), the shared [layout contract](../init/references/project-layout.md), and any explicitly selected or layout-discovered boundary file. Apply it to source reads, local output, delegation, and remote delivery; do not start Init automatically. Missing boundaries allow only existing explicit authorization or work in chat, as the contract describes.

Read and follow [Glossary](../glossary/SKILL.md), unless already loaded in this context. Locate or establish the relevant glossary before drafting and use its agreed terms. Resolve linked paths relative to this skill's folder. If this required dependency is missing, report the missing path and request its restoration before continuing the dependent workflow.

Read and follow [Search](../search/SKILL.md) when factual retrieval is needed, including its permission checks, bounded worker, direct-lookup fallback, and result limitations. Read and follow [Refine](../refine/SKILL.md) for every unresolved substantive user choice. Refine is a conditional dependency: material that is already ready can be documented without a prior Refine session.

## Establish the writing brief

Infer the purpose, audience, required coverage, document type, working language, detail level, format, and destination from the request and existing material. Use sensible defaults for routine editorial choices such as a title. Record material ambiguity for resolution through the readiness process below. Routine delivery questions and access approvals may be handled directly.

Respect the requested delivery mode: a document in chat, a local file, or a specified document format. Follow established topic or project locations. For a requested saved document with no specified format, use Markdown in the host's established human-document location, or the kit's reader-facing document area when no suitable host location exists, and state the chosen filename. If no usable destination exists, identify saving as outstanding and deliver in chat only after the substantive readiness requirements are met. A request to plan a document does not authorize creating the document itself.

## Establish readiness before drafting

Use Project Context preparation when available under the ownership contract, then inspect the designated decision record and separate checkpoint, relevant conversation, glossary, and necessary source artifacts. Project Context freshness does not satisfy this skill's substantive readiness gate. Identify the content the brief requires and the evidence supporting it. Prefer explicit user corrections and later agreements over superseded proposals; treat conflicts with unclear precedence as gaps. Reuse a suitable existing record rather than copying accepted choices into another decision log.

Distinguish established facts, user-provided context, agreed decisions, preferences, proposals, and unknowns. Preserve source attribution where factual support matters. Do not invent commitments, dates, budgets, quotations, agreement, or evidence to fill missing information.

Resolve every substantive gap before drafting any part of the document. Preparing the writing brief, inspecting sources, and listing gaps are permitted before readiness. A placeholder or a label such as "unknown" does not by itself close a gap.

Uncertainty or a proposed term can be legitimate document content when its treatment is established by the brief and its status remains explicit. If its unresolved meaning would change required content or conclusions, it remains a substantive gap. Follow Glossary for terminology decisions.

## Resolve gaps and resume

Use Search to retrieve missing factual evidence from authorized sources. Interpret its results and coverage yourself. Ask the user for necessary personal or situational context that those sources cannot supply. An unsuccessful or blocked search leaves a necessary factual gap unresolved; report the limitation without inventing certainty or asking the user to research retrievable facts.

Take every unresolved substantive user choice through an assigned-choice Refine handoff, including choices needed to settle conflicting interpretations or change the brief. Follow the ownership contract's input and return requirements, preserving the same record and glossary. Refine returns to this pending invocation; let the responsible owners apply their artifact updates and resume from the checkpoint.

Include verified evidence and Refine's resulting decisions in the source material, then recheck the brief, glossary, and all substantive gaps. Proceed to writing only when every substantive gap is closed. An agreed change to the brief may remove a requirement; do not silently narrow the scope to declare readiness.

If a required dependency, source, authorization, or user decision remains unavailable, report the specific blocker and the next needed action. Leave document drafting pending. If a user question has been posed, pause all task preparation as well until its answer or an explicitly authorized recommended-answer assumption resolves it under the boundary contract.

## Write a faithful, complete synthesis

Organize around what the intended reader needs to understand or do. Reorganize, condense, and explain the established material while preserving its meaning, agreement status, and necessary qualifications. Do not introduce substantive requirements, decisions, recommendations, or factual claims beyond the established source material. Relevant proposals already present in the sources may be included with their status clear.

Cover every requirement in the agreed scope with the detail necessary for the purpose and audience. Use only useful sections and an appropriate structure for the topic. Keep the glossary and discussion record separate unless the deliverable benefits from including them.

Use the relevant available format-specific capability for Word, PDF, or other requested output without changing the agreed substance. If writing or verification reveals a new substantive gap, suspend document work and resolve it through the readiness process before continuing.

## Verify, deliver, and revise

Check the document against its brief and sources: full required coverage, glossary consistency, agreement status, contradictions, factual support, audience fit, format, and remaining drafting placeholders. Correct editorial discrepancies directly; unresolved substantive user choices return through Refine. Do not claim verification that the available evidence or rendering capability could not support.

Deliver the document or its file link with any material verification or delivery limitations. Supply its actual applied/verified status to the caller's checkpoint; when acting as caller, maintain that checkpoint if writing is permitted. Completeness requires the agreed coverage and resolved substantive gaps; a partially written document or a list of placeholders is not a completed deliverable. Delivery preserves the decision record's authority. A local document request does not authorize external publication or sending it to others.

For revisions, apply the same readiness requirements to the requested change and preserve unrelated content. Reconcile changed definitions or decisions with the glossary and discussion record using their agreement rules. An explicit user correction can settle a change; any substantive choice still unresolved must go through Refine before editing document content.
