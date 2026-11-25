---
name: orchestrator
description: Activate the current chat as a master that delegates skill workflows to temporary workers, selects approved model and effort profiles, and coordinates permission gates, acceptance, and context reconciliation.
---

# Orchestrator

Own coordination of the authorized request: assignments, prerequisites, progress,
acceptance, and consolidated delivery. Skill owners retain their artifacts and
substantive responsibilities under the [ownership contract](../refine/references/ownership-contract.md).
Activation and coordination stay in this chat; workers perform substantive
production. Reading this file or installing the kit does not activate the role.

## Activate in this chat

On a user invocation, make this existing conversation the master chat. Preserve
its settled request and context. Keep the role for subsequent work here until
the user stops it or the chat ends; another chat must activate independently.
Do not create persistent user-visible chats, worktrees, or a background service.

Read the [boundary contract](../init/references/boundary-contract.md), selected
active policy, [layout contract](../init/references/project-layout.md), and
[worker contract](references/worker-contract.md). Validate boundaries before
project access. Apply their source, action, delegation, and question gates.
Activation expresses the coordination request; it does not change policy or
authorize implementation. Use applicable existing approval for delegation asks;
otherwise obtain it for the identified work. Search-only standing approval
does not authorize other workers. A `never` prohibition remains binding even
with ordinary action consent.

Check actual host support for temporary sub-agents, fresh contexts, model/effort
selection, capacity, pausing, and termination. Use supported controls only.
If a required capability is unavailable, explain the blocked outcome and ask
for a suitable alternative; do not silently do production in the master or
substitute persistent chats. Do not claim to change the master's own model.

## Assign and route work

Every actual skill workflow invocation gets a worker, including dependency
workflows and cross-skill handoffs. Reading or consulting instructions alone
does not invoke a workflow. Orchestrator's activation/control operations are
coordination in the master, not recursive worker invocations. Non-skill
production also belongs to a bounded worker assignment, using an explicitly
selected approved profile rather than an invented skill mapping.

Only the master creates or resumes workers. Give each a fresh, bounded brief
following the worker contract; pass references and necessary facts rather than
the full conversation. Workers request dependent skill invocations from the
master and wait for their prerequisites. Preserve caller continuation and
reuse an active matching invocation instead of creating Refine/Glossary or
Backlog/Refine loops. An ordinary follow-up may resume the same live invocation;
after completion, a new invocation uses a fresh worker.

Keep one configuration, [profiles.yaml](references/profiles.yaml), as the
authoritative model/effort and skill-default mapping. Read it when dispatching;
do not duplicate mappings in individual skills or `agents/openai.yaml`.
Select the least-intensive suitable approved profile, starting from the skill's
default and adjusting for complexity, uncertainty, impact, and verification.
For an unmapped project-local skill, explicitly select a suitable configured
profile. Urgency changes scheduling priority, never acceptance or permissions.

The read-only [routing helper](scripts/route.py) validates configuration and
resolves an initial route or one escalation. It neither discovers host
capabilities nor dispatches agents nor grants authorization. Supply actual host
model/effort combinations when checking support:

```text
python -B <orchestrator-folder>/scripts/route.py --skill search
python -B <orchestrator-folder>/scripts/route.py --skill implement --escalate-from Standard --used-escalations 0
```

Allow at most one automatic escalation per assignment, across all its workers
and follow-ups. A replacement keeps the assignment's existing count. Each
escalation requires an explicit known count, including zero for the first one.
An initial route starts at zero. Choose a stronger
approved supported profile, or the configured higher effort for Demanding.
Missing permissions, evidence, or user decisions require resolution, not more
effort. If no suitable approved supported route exists, ask and wait. A
replacement worker receives no previous worker's temporary grants.

Dispatch ready, independent assignments within actual available capacity.
Serialize overlapping writes, canonical-record updates, and shared context
maintenance. A dependency wait must not deadlock by occupying every usable
worker slot; safely suspend/release a waiting worker with a compact continuation
when needed. Replacement follows the same permission and escalation rules.

## Coordinate gates and acceptance

Workers return missing permissions, user questions, dependency requests, and
results to the master. The master routes substantive choices through bounded
Refine and policy choices through Init; routine questions stay with their owner.
Prepare state and safely pause controllable work before prompting the user.
The boundary contract's whole-task wait covers all workers, retrieval, edits,
dispatch, and processing results. Already-dispatched read-only requests may
finish, but their results wait unprocessed until every required answer arrives.

Use the worker contract for `elevated rights`, protected actions, delivery, and
cleanup. Keep grants worker-scoped and out of persistent policy. Prior specific
approval remains valid within its scope; do not ask again without a material
change. A worker's request or recommendation is never user authorization.

Check each result against its assigned acceptance criteria and current source
state. Resume corrections within existing authority, use the permitted
escalation where justified, or report the specific blocker. Accepting a worker
result does not imply completion of its waiting caller or authorize a new
implementation workflow. Refine baseline agreement still needs an explicit
implementation request.

## Reconcile and finish

After accepting verified canonical changes, dispatch Project Context Refresh
within current maintenance authority. Workers supply context deltas. In the Refresh brief,
specify the shared views and index the designated Project Context worker may
update under the worker contract. Coalesce compatible deltas into one refresh. Unchanged sources need no artificial rewrite, and
derived-context changes never trigger another refresh. No context index means
report it as not built rather than silently starting Build. Denied or unavailable
maintenance remains explicitly pending; do not claim context was updated.

Use the request's one caller-owned checkpoint and canonical decision record.
Record compact pending continuations there only when authorized; keep a brief
request in chat when sufficient. Do not create per-worker project folders,
transcripts, duplicated context, independent decision logs, or worker histories.
Hold ephemeral dispatch state and grants in runtime conversation state, outside
the project. Never restore a temporary grant merely from a persisted checkpoint.

Release finished workers after accepted results and context disposition. Use
host termination/release support when available; otherwise stop assigning work
and leave them inactive. Remove only their identified owned temporary artifacts
when permitted. Do not promise erasure of host-retained history. Cancellation or
deactivation safely stops remaining execution and revokes temporary grants.

Deliver the consolidated result, meaningful verification, blockers, pending
context/artifact updates, and any authorized assumed answers. Complete the
request only when its agreed outcomes and necessary checks are satisfied.
