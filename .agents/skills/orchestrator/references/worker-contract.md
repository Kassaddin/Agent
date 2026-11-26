# Orchestrator Worker Contract

Apply this only in a chat with Orchestrator active and its assigned temporary
workers. The [boundary contract](../../init/references/boundary-contract.md)
and current policy still govern all effects. This contract creates no standing
delegation permission and grants no production or implementation authority.

## Assignment and continuation

The master alone dispatches. Supply the invocation/assignment identity, skill
path and operation, bounded objective and scope, prerequisite state, canonical
decision/glossary/source references, selected boundary path, permitted resources
and effects, approved profile, acceptance criteria, and expected return.
Include any applicable actual approval with its exact scope. Pass only what
the worker needs; omit unrelated personal context and credentials. Fresh context
does not imply a host security sandbox or revoke instructions imposed by the host.

Tell the worker it is not the master and must not spawn children, expand scope,
contact the user directly, perform unapproved production, or write master-owned
coordination state. Loading a dependency's instructions is permitted within
access authority. To perform a dependency workflow, request a worker from the
master. Return a compact continuation before safe suspension. Resume only after
the master provides the resolved prerequisite.

For shared context maintenance, only the designated Project Context worker
assigned an authorized Build or Refresh may write the views and index specified
in its brief and the [Project Context instructions](../../project-context/SKILL.md).
The brief must identify the permitted output paths in the selected agent area or
established legacy layout. Project Context Load is read-only. Search, Smokes,
and other workers have no shared-context maintenance authority.

Dependency requests identify the needed skill/operation, assigned scope, settled
references, evidence, and expected result. Reuse a matching active invocation
when possible. Finishing a handoff returns to the waiting caller rather than
starting its workflow again. Reading canonical glossary entries is not a
Glossary-maintenance invocation. Search workers retrieve directly in their
assigned context instead of creating an extra Search worker.

Workers return question or permission requests to the master before affected
work. Requests do not count as user questions until the master presents them,
but the worker must stop the affected operation immediately. When the master
applies the shared question rules, pause controllable work at a safe boundary
and preserve recovery evidence for in-flight mutations. Do not pretend an issued
write can be undone by cancelling a request. Pending read-only results remain
unprocessed throughout the whole-task question gate.

## Temporary elevated rights and protected actions

Use the [Init elevated rights contract](../../init/references/elevated-rights-contract.md)
for activation, covered effects, protected actions, and expiration. Activation
is a master control operation. Include the recipient's declared scope in the
live assignment only after the master has handled the user's grant and notice.

## Return, context, and release

Return the assignment identity, result/deliverable references, actual changed
artifacts, verification evidence and limits, blockers/questions, pending owner
updates, necessary continuation, and relevant canonical-source/context delta.
Preserve the owning skill's structured result, including Search coverage or
Smokes findings; no additional persistent worker-report format is required.

Workers edit only their authorized owned/delivered artifacts. Search and Smokes
retain source-write restrictions. No per-worker source logs or checkpoint
copies are created. Use an authorized temporary workspace only when needed,
and identify owned temporary artifacts for permitted cleanup. Shared context
reconciliation belongs to a separate Project Context invocation after master
acceptance. Its own derived output is not a new source-change event.

Return quietly to the master, honoring unavoidable host notices. A worker does
not declare itself released before its caller has a usable result. The master
records acceptance and context disposition, then ends active execution/releases
resources where supported. Pending context work is explicit when unavailable or
unauthorized. Release never claims deletion of host-retained history.
