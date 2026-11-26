---
name: glossary
description: Establish and maintain a project or topic glossary when defining terms, resolving ambiguous language, or keeping terminology consistent during idea refinement and document creation.
---

# Glossary

Maintain a shared vocabulary for the current project or topic. This skill owns definitions; the surrounding workflow owns decisions, actions, and deliverables. It works independently and is also the required terminology dependency of `refine` and `to-document`.

Refine resolves unresolved substantive content choices, including disputed meanings, under the [ownership contract](../refine/references/ownership-contract.md). Load that contract only when a handoff or persistent-state operation needs it. This skill records the agreed definition and agreement status; the topic's decision record retains the decision and reason.

## Locate and scope the glossary

Before project-resource access, read and follow the shared [boundary contract](../init/references/boundary-contract.md) and [layout contract](../init/references/project-layout.md). Use the explicitly selected or layout-discovered boundary file when present. This dependency interprets access rules; it does not run the Init interview automatically. If boundaries are missing, keep work within existing explicit authorization or in chat as the contract describes.

Use a glossary explicitly selected by the user. Otherwise inspect the active project's guidance and existing glossary locations. Reuse a glossary only when its scope matches the current topic; do not collect unrelated projects in a personal master glossary.

Reuse the host's established glossary. For a new standalone topic without a suitable location, propose `docs/glossary.md` under the selected kit/repository root. Keep the glossary reader-facing and follow an established project layout when one exists. State a new location before writing; ask only when competing locations would materially change ownership or scope. If there is no usable working folder, maintain the glossary in the conversation until a destination is established.

The glossary is required throughout refinement and document creation. Establish it at the start and maintain it as meanings become clear. For read-only, planning-only, or no-file requests, keep the glossary in the response or conversation and identify it as unsaved. An existing file needs no edit when its definitions already suffice. Do not invent entries to populate an empty glossary.

## Resolve meanings

- Read the relevant definitions before naming concepts. Use agreed canonical terms consistently.
- Identify ambiguity when different meanings would change the reasoning or outcome. State the unresolved choice and propose meanings with their implications. Under a caller, return that gap so it can use Refine; for a standalone request, act as the caller and use [Refine](../refine/SKILL.md) only for the assigned substantive choice. Reuse an active relevant refinement. If it is unavailable, report the dependency and leave the meaning unresolved. A user question pauses the entire task under the boundary contract.
- Distinguish user agreement from an agent recommendation. An inferred meaning may be recorded as proposed, never silently promoted to agreed. Explicit acceptance or an unambiguous definition supplied by the user can establish agreement.
- When a later statement conflicts with an agreed definition, surface the conflict and resolve the intended scope or change. Preserve the existing agreed definition until a replacement is agreed.
- The same word can legitimately have different meanings in different contexts. Qualify the terms or separate the glossaries instead of forcing one definition across contexts.
- Use sources when the meaning depends on external facts or an authoritative definition. A locally agreed definition establishes usage for this topic, not universal factual truth.

Read [glossary-format.md](references/glossary-format.md) when creating or changing entries. Preserve compatible existing formats rather than rewriting an entire glossary for presentation alone.

## Capture and reuse

Record each resolved term promptly when local artifact creation is within the task's scope. Keep definitions concise and in the user's working language. Include common words when their specific meaning matters to this discussion; avoid cataloguing ordinary words that cause no ambiguity.

Keep implementation plans, decisions, evidence logs, and open action items outside the glossary. Do not overwrite unrelated entries. Report material terminology changes briefly in the surrounding workflow's update or handoff.

When called by another skill, return the glossary location or inline content, applicable agreed terms, unresolved terminology, and actual update/verification status for its checkpoint. Preserve the caller's continuation; do not start its full interview or generate its final document. An explicit accepted definition can be recorded directly without reopening its settled meaning.
