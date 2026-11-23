# Ownership, Handoffs, and Resumption

Apply this contract when resolving substantive content choices across skills, maintaining a topic's decision record, or resuming its work. It is shared workflow guidance; it grants no additional access, execution, delegation, or implementation authority. Apply the Init boundary contract and current project boundaries to every affected operation.

## Owners and corrections

**Owner:** The skill responsible for the meaning, consistency, and maintenance of a specified kind of information or artifact.

| Skill | Owned information or artifact |
| --- | --- |
| Init | Boundary configuration and access-policy consistency |
| Glossary | Canonical definitions, aliases, and terminology agreement status |
| Refine | Refinement process, decision rationale, and MVP baseline |
| Implement | Authorized execution of agreed small-task baselines, verification evidence, and implementation outcomes |
| Create Skill | Project-local skill authoring, supporting resources, and validation; host registration remains separate |
| Backlog | Captured project backlog entries, their provenance, and capture/deduplication consistency |
| Search | Retrieved evidence, verified locators, and retrieval coverage |
| To Document | Document composition, faithful representation, and delivery completeness |
| To Tasks | Task decomposition, task boundaries, requirement coverage, and dependency consistency |
| Smokes | Audit findings, evidence, classifications, and coverage |
| Fix | Authorized corrections, verification evidence, and correction outcomes |
| Context | Derived project views, source index, and freshness information |
| Setup | First installation, installation verification, and setup/recovery outcomes |
| Update | Release comparison, shared release/receipt protocol, later managed-file replacement, and update/recovery outcomes |

The user remains the substantive decision-maker. Refine is the common resolution workflow for unresolved substantive content choices; the responsible owner supplies its constraints and records the resulting change in its artifact. Init continues handling access-policy choices. Routine delivery and access questions remain with the responsible workflow.

**Mechanical correction:** A correction whose intended result is unambiguously supported by current authoritative material and preserves agreed meaning, scope, and requirements.

Fix may apply an authorized mechanical correction directly and verify it without starting the owner's full workflow. A choice between plausible meanings or targets requires resolution through Refine first. Implement may correct its own authorized in-scope work and verify it without starting a report-based Fix workflow. Corrections requested from a Smokes report remain Fix's workflow. Ownership is accountability; current permissions and the requested task still determine whether any edit is permitted. A handoff does not itself authorize another agent.

## One decision record per topic

Use the topic's designated reader-facing record for accepted choices and reasons. Reuse a suitable existing host record. For sustained refinement without one, propose `docs/topics/<topic>/decisions.md` under the selected kit/repository root. A short or no-file discussion can designate the current conversation as its record; identify unsaved state explicitly.

Preserve a record belonging to another topic; use the established topic location or a clearly named topic record instead of overwriting it.

Refine maintains decision entries. Keep them distinct from proposals, assumptions, facts, and pending actions. Refer to canonical definitions in the glossary rather than maintaining another independently editable definition. Owners maintain their artifacts; delivered documents represent accepted decisions faithfully and do not replace the decision record as their authority.

An agreed decision and an applied artifact update are separate states. Preserve decision references when applying or verifying an update. Reopen settled choices only for material new information or an explicit user revision. Record the revised accepted choice and reason so superseded content is not treated as current.

## Deferred items

[Backlog](../../backlog/SKILL.md) owns captured out-of-scope items in one reader-facing
project file. It is active only in conversations where Backlog or Refine was
invoked, not from project adoption or a context summary alone. When capture is
already active, a caller can supply an item and receive its ID and actual saved
or unsaved status; caller write restrictions still apply. Search and Smokes never
gain backlog-write authority through that handoff.

Accepted choices and exclusion reasons remain in the topic record; the backlog
retains the item and source references. Capture is not approval, prioritization,
implementation authorization, or resolution of a required prerequisite. Link the
existing sources instead of creating another decision log or checkpoint.

## Assigned-choice handoffs

The caller retains responsibility for the surrounding request, continuation, and delivery. Pass only:

- Assigned choices and the relevant objective and scope.
- Owner constraints, settled decision references, and the designated record.
- Necessary evidence, glossary, and artifact references.
- The expected return result and pending continuation.

Refine resolves only those choices and their necessary dependencies, reusing settled information. If a newly discovered issue requires expansion of the agreed scope, surface it explicitly rather than silently enlarging the task. Continue an already active relevant refinement instead of starting another interview.

Return accepted decisions and reasons, their record references, remaining blockers, and pending artifact updates. Record the decisions, let each owner supply the actual update status, and let the caller resume. A bounded Refine call never starts a new invocation of its waiting caller or declares the entire outer request complete merely because its assigned choices are settled.

## Resume checkpoint

**Resume checkpoint:** A compact record of the active request, relevant decision references, current step, blockers, pending artifact updates, and next action.

Keep one separate checkpoint in the selected agent area's `state/checkpoints/<topic>.yaml`, linked to the designated reader-facing decision record. Follow the [layout contract](../../init/references/project-layout.md) and [checkpoint schema](checkpoint.schema.json). Include the active objective and agreed scope, caller and current handoff, settled decision references, remaining gaps and blockers, artifact update states, next action, and any required user input.

| Information | Responsible skill |
| --- | --- |
| Accepted decisions and reasons | Refine |
| Objective, scope, caller, current step, handoff, blockers, and next action | Caller |
| Actual artifact update and verification status | Artifact owner |

Record an update as pending, applied, or verified according to evidence. Agreement alone does not establish application; application alone does not establish successful verification. Preserve unrelated record sections and concurrent edits.

Resume from the checkpoint and its references. Retrieve source material relevant to the current step or a concrete verification need, and reload changed boundaries before affected operations. A stale or incomplete checkpoint is a reason to inspect relevant sources, not to invent state or repeat settled questions automatically.

Checkpoint writes require authorization and must respect the active workflow's write limits. Search and Smokes return status or a checkpoint delta to their caller; they never edit source records to preserve progress. In planning-only or read-only work, keep the checkpoint in the designated conversation or return an explicitly unsaved update for the existing checkpoint. Accepted choices and reasons remain in the reader-facing record.

## Context preparation and refresh

When project context is available, the caller may use [Context](../../context/SKILL.md) Load to obtain a bounded view for the current request before detailed work. Load is read-only. Use current boundaries and the designated record/checkpoint; context summaries do not establish permissions, agreement, document readiness, or completion. Missing context is not a reason to force Build or repeat settled discussion.

The caller resolves remaining substantive choices through assigned-choice Refine, lets owners apply and verify changes, and maintains its checkpoint. It may then request Context Refresh for affected sources when maintenance is already authorized. Otherwise record the needed refresh as pending. Search/audit write restrictions remain unchanged; a retrieval or audit request grants no Context write authority.

Context updates only its derived views and index. It returns gaps, conflicts, source references, and freshness/coverage limits to the caller. It does not maintain another decision log or checkpoint, rewrite canonical records, or trigger refresh from its own output changes.
