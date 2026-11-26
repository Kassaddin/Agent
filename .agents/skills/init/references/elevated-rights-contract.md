# Elevated Rights Contract

Init owns the meaning of permission decisions. Apply this contract with the
[boundary contract](boundary-contract.md) and current project policy.

## Activate and declare scope

Use only a direct user instruction to activate `elevated rights` for the current
task, in the initial request or during operations. Quoting the phrase, discussing
it, or reading or installing the skill leaves consent unchanged.

In ordinary chat the agent performing the task is the recipient. In active
Orchestrator mode the master handles activation as a control operation for one
identified worker and its current assignment. Use the worker that unambiguously
owns the requested work. If the initial request arrives before dispatch, retain
the instruction in live coordination state. Dispatch the task through the usual
authorized workflow and then handle the grant for the unambiguous assigned
worker. Activation adds no delegation authority, extra worker, or grant for
the master. A worker refers the user instruction to the master and waits for
its decision before relying on the grant.

Derive the permitted resources, operations, and expected effects from the settled
task or assignment and approved boundaries. If the intended recipient, task, or
scope is materially ambiguous, resolve the ambiguity under the
[question rules](boundary-contract.md#questions-and-assumed-answers) before
activating. In particular, if several workers could receive the grant, identify
which one the user intends. State the task or assignment, recipient, concrete
resources, operations, and covered effects to the user before relying on the
grant. Include queued changes and their destinations in that notice when known
and notifications are enabled. Notify any later queued changes and destinations
before the corresponding writes under the normal boundary rule.

## Apply to actual effects

The grant can satisfy ordinary local `ask` decisions for known non-protected
effects within the declared scope. Check every effect of a command or operation.
For example, a known local validation command or deletion of a disposable
task-generated output can qualify. Classify dependency operations and CI changes
by their actual effects, including changes to shared environments, disclosures,
and any consequential execution or automation. Investigate unknown effects
through authorized checks before relying on the grant.

### Protected actions

**Protected action:** An operation with material potential for data loss,
changes to active security or privacy controls, disclosure of personal or
confidential information, or commitments beyond existing authorization.

Examples include deleting user data or truncating a database; overwriting an
unrecoverable original; discarding work, rewriting history, or force-pushing;
changing active security settings, credentials, or access controls; obtaining
administrator privileges; exposing secrets or confidential data to another
recipient/service; publishing, production deployment, purchases, or new paid
resources beyond existing authorization; and widening persistent trust or
access policy. Assess actual effects and existing authorization. Protected
actions require specific user authorization covering those effects, which can be
reused while valid and within scope.

### Other gates

The grant supplies local project consent only. Apply `never`, `user_only`,
read-only sources, technical access limits, platform prompts, higher-priority
instructions, remote-write gates, version-control rules, delegation decisions,
implementation approval, and skill ownership independently. Obtain explicit
authorization and use Init review for policy changes. Apply the shared question
rules when a decision or approval is required. Unattended execution and
permission to assume a recommended answer each require a separate user
instruction.

## Duration and transfer

Keep the live consent and scope in ephemeral conversation or coordination
state. Never save an active grant in project files, policy, reports, or
checkpoints, or restore it from summaries, historical messages, or persisted
state after session or live-context loss.

Expire the grant on task or assignment completion, cancellation, revocation,
recipient replacement, material rescoping, or session or live-context loss.
A worker grant also expires when Orchestrator mode ends. A follow-up to the
same live worker may continue within the original assignment and scope. The
grant never transfers to another task, agent, worker, replacement, dependency,
master, or later invocation.

## Existing project protocols

Before relying on the grant, verify current boundaries and read any applicable
local protocol explicitly referenced by configured project guidance. Follow
only those references within authorized project scope. Reuse compatible local
rules and retain their host files and integration during Setup and Update.
Local records of accepted decisions establish local intent only.

Before applying a Setup install, host integration, or Update preview, check
the exact planned changes against the existing explicitly referenced protocol
files and guidance pointers. Stop a change that would replace a local protocol,
remove or break a pointer, or change how the protocol applies. Resolve that
impact before proceeding with the affected change.

If a difference materially affects consent, required approvals, or behavior,
surface it and resolve the affected choice through Refine, or Init for a policy
choice. Preserve the existing files and wiring while the conflict is unresolved.
Setup or Update cannot silently replace, migrate, relax, or bypass a local
protocol. A local protocol cannot broaden the kit grant or the project policy.
