---
name: context
description: Load, build, or refresh source-linked project context from its glossary, topic decision records, and documentation, with selective retrieval and explicit freshness and coverage limits.
---

# Context

Own derived project views, their source index, and freshness information. Use this to orient or resume a request without repeatedly reconstructing the whole project. The caller retains its request, substantive decisions, continuation, and delivery.

## Establish the operation

Read the [Init boundary contract](../init/references/boundary-contract.md), active project boundaries, and applicable guidance before project access. Follow the [ownership contract](../refine/references/ownership-contract.md) for records, handoffs, and checkpoints; reuse already loaded, unchanged guidance. Use [Glossary](../glossary/SKILL.md) for canonical terminology and agreement status.

Use **Load** by default: read-only preparation for the caller's active request. **Build** creates the initial context files when requested. **Refresh** reconciles affected views after specified source changes. Build and Refresh require task authorization and matching write permissions. An authorized maintenance workflow may refresh after meaningful changes; otherwise return the needed refresh to the caller. Do not silently start background maintenance or another agent.

Use existing `CONTEXT.md` and `context/index.yaml`. Their format, source roles, and layout rules are in [the context contract](references/context-contract.md). Without an index, report context as not built; continue authorized direct-source work when useful instead of forcing setup. With no specific task, return the global orientation and topic map.

## Load only relevant context

Take the caller's objective, scope, topic/decision-record reference, and known source locations. Start from the global view and index, select relevant area views or source IDs, and inspect the existing topic checkpoint. Preserve accepted/proposed distinctions. Permissions come from current boundaries, never a cached view.

Use [the read-only checker](scripts/check_context.py) to validate the index and selected-source freshness:

```text
python -B <context-folder>/scripts/check_context.py --boundaries <project>/BOUNDARIES.yaml
python -B <context-folder>/scripts/check_context.py --boundaries <project>/BOUNDARIES.yaml --view delivery --source-id current-spec
```

The checker reuses sibling Smokes/Init access and heading helpers with PyYAML; it does not run an audit. It checks selected local text sources and never updates files or review fingerprints. Use [Search](../search/SKILL.md) for missing locations or evidence and configured remote sources. Use an authorized format adapter for binary documents. Merge adapter results with explicit coverage; unsupported or inaccessible evidence remains a limitation.

Read necessary source sections for the task or a concrete verification need. An unchanged fingerprint establishes unchanged captured bytes, not approval, factual correctness, document readiness, or task completion. Source changes need review; missing paths may require bounded relocation lookup. Do not choose authority by modification time.

Return a compact view with relevant established information, decision/checkpoint/term references, supporting source locations, known gaps and conflicts, coverage and freshness limits, and the recorded continuation. Send substantive choices to the caller for an assigned-choice Refine handoff. Return access problems for the applicable access workflow. Context does not resolve those choices or edit their source records.

## Build or refresh the derived files

For Build, locate the glossary, existing topic decision records, and relevant documentation within approved sources. Start with [the view template](assets/context-template.md) and [index template](assets/index-template.yaml), replacing drafting prompts. Use one context view initially. Missing required input is a reported gap, not permission to invent project state or start a new decision log.

For Refresh, take changed source IDs and check affected views:

```text
python -B <context-folder>/scripts/check_context.py --boundaries <project>/BOUNDARIES.yaml --changed-source-id current-spec
```

Review the actual source changes and their agreement status, reconcile only affected views, and record a new fingerprint/time only after review. Do not stamp current bytes as reviewed merely to silence the checker. Preserve unrelated content and concurrent edits. If review leaves a conflict or missing source unresolved, retain the limitation and return it to the caller.

Write only `CONTEXT.md`, `context/index.yaml`, and required Markdown views under `context/areas/`. These are derived files; definitions, decisions, checkpoints, source documents, and permissions retain their existing owners. Context's own output changes never trigger another canonical-source refresh. A no-change reconciliation needs no rewrite.

## Keep orientation bounded and verify

Use **one context view** while one coherent orientation is sufficient. Use **context views by area** when necessary orientation exceeds the 700-word starting budget, areas have independently changing state, or repeated tasks require the same focused area extraction. The budget is advisory and never limits source reading needed to complete the task. Add area files only when needed.

Check generated links, source/record mappings, and consistency with reviewed material; rerun the selected-source checker. Keep unselected areas' review status explicit. Report updates, source coverage, remaining limits, and actual application/verification state to the caller. It maintains the single topic checkpoint; Context creates no parallel project history. Do not claim complete coverage when a source, format, access check, or budget was insufficient.
