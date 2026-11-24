---
name: to-tasks
description: Split a documented idea into bounded functional or enabling tasks traced to one agreed Refine baseline, with explicit prerequisites and acceptance criteria for later implementation.
---

# To Tasks

Own task decomposition, task boundaries, requirement coverage, and dependency
consistency. Work across topics from a documented idea and its agreed parent
[Refine](../refine/SKILL.md) baseline. The document may have been produced earlier
by [To Document](../to-document/SKILL.md); there is no mandatory or automatic
sequence between documentation, decomposition, and implementation.

## Establish scope and access

Read the shared [boundary contract](../init/references/boundary-contract.md),
current selected policy, [layout contract](../init/references/project-layout.md),
and [ownership contract](../refine/references/ownership-contract.md). Follow their
question gate, handoff, and state rules. Missing boundaries grant no permissions
and do not start Init automatically. Access-policy choices remain with Init.

Use [Glossary](../glossary/SKILL.md) for the relevant agreed meanings. In this
workflow, a **functional block** is a coherent part of the documented scope with
a distinct functional or enabling outcome that can be verified once its
prerequisites are satisfied. Inspect the document, parent baseline, and relevant
decision references; use [Search](../search/SKILL.md) when evidence needs retrieval. Project Context may help
locate sources but does not establish agreement or readiness. Report unavailable
required dependencies rather than silently substituting a different contract.

Require one agreed parent Refine baseline covering the requested documented
scope; its agreement may be recorded in the conversation or designated topic
record. A document's existence alone does not establish that agreement. Reuse it
for every task instead of requiring a new full refinement for each one. Resolve
material conflicts between the document and baseline through bounded Refine.

## Decompose into functional blocks

Give each task one distinct functional or enabling outcome, bounded scope,
identifiable prerequisites, and acceptance criteria that can be checked directly
once prerequisites are satisfied. Foundation work may stand alone without a
user-facing feature. Split further when a task lacks those properties; do not
use numerical size limits or divide solely by file, technical layer, or work phase.

Cover all agreed requirements, including necessary integration work. Give each
piece of work a clear responsibility; reference shared prerequisites rather than
repeating their work in several tasks. Include only tasks necessary for the
requested scope, without inventing features, priorities, estimates, or lifecycle
management. Necessary prerequisites remain visible even when outside the work
this plan can perform; do not hide them as optional deferred work.

New substantive content choices go through an assigned-choice Refine handoff,
reusing the existing record and returning to this invocation. Record decisions
and reasons there; keep operational blockers in the caller's existing checkpoint.
Reference those records instead of adding task-local blocker histories. A user
question pauses the whole current task under the boundary contract.

An outstanding prerequisite implementation does not make a task insufficiently
defined. An unresolved substantive choice affecting its outcome or requirements
does: leave the affected brief pending and report the gap, rather than presenting
an unresolved placeholder as ready for Implement.

## Write a uniform task set

For each source document, create a sibling folder named
`[document-name]-tasks`, using its filename without the extension. Keep all its
task files there, in the reader-facing document area. For an unsaved document,
establish its name and authorized destination before writing; a planning-only
request keeps the proposed task set in chat. Preserve existing task files and
unrelated content; resolve an ambiguous existing plan rather than replacing it.

Use [task-template.md](assets/task-template.md) for every task. Its title supplies
the required ID and name; its five following sections are required. Retain the
two optional sections only when they clarify this task. Remove template prompts
from delivered files. Explicitly write `None` for absent prerequisites.

Start IDs at `00`; use at least two digits and a unique, descriptive filename
such as `00-establish-data-foundation.md`. Keep assigned IDs stable, including
when prerequisites change. Numbering is an identifier, not execution authority
or a substitute for explicit prerequisite links and required outcomes.

Scope references establish the task's agreed meaning and requirements. They
grant no access or action permissions. Apply the current `BOUNDARIES.yaml`
independently before affected operations.

Link each brief to its parent baseline and relevant document sections or
requirement IDs, and to glossary entries only where useful. Use real locators;
identify conversation references honestly when no saved record exists. Describe
the task-specific requirements without copying shared context, definitions,
decision histories, or boundary rules into the brief. Do not create an additional
index, specification, or tracking file merely to repeat the task contents.

Acceptance criteria state observable conditions for this task's agreed result.
Use minimal verification to establish those criteria. Additional border-value
and extreme-case testing is outside this flow; do not enlarge the criteria to
introduce it. Optional verification constraints specify only a necessary method,
environment, or evidence standard whose omission would leave acceptance unclear.
Routine execution and verification procedures belong to Implement.

## Check coverage and deliver

Before delivery, check that every agreed requirement maps to a task, each task
has its required fields and source traceability, names and IDs are distinct,
prerequisite references resolve, and the dependency graph has no cycles. Check
that task responsibilities do not overlap unnecessarily and their acceptance
criteria can establish the required outcomes. Correct in-scope decomposition or
link errors; new substantive choices return through Refine.

Return the task-folder link, a concise requirement-to-task coverage summary,
dependency order or independent groups, and any unresolved gaps or delivery
limits. Keep this summary in the delivery rather than maintaining another copy
of task state. Supply actual artifact status to the caller's single checkpoint
when sustained work needs one. Partial coverage or unresolved affected briefs
must be reported as incomplete.

Tasks inherit the parent's agreement only within its settled scope. Their
creation or approval does not authorize execution. On a later explicit
[Implement](../implement/SKILL.md) request, pass the selected task, parent baseline,
scope references, and prerequisites; Implement checks current readiness,
permissions, and actual acceptance evidence. Do not automatically execute tasks,
publish documents, install skills, or start Smokes/Fix.
