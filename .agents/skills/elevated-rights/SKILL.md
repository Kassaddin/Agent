---
name: elevated-rights
description: Handle an explicit elevated rights command for scoped, temporary consent under the project's boundary policy during an active task.
---

# Elevated Rights

Act on a direct user instruction to activate `elevated rights` for the current
task, in the initial request or during execution. Reading this skill, quoting the
command, or discussing its meaning leaves grant state unchanged.

Read the [elevated rights contract](../init/references/elevated-rights-contract.md),
the [boundary contract](../init/references/boundary-contract.md), and the selected
project policy. Consult any configured project-local elevated rights protocol
and resolve conflicts under the contracts before activating a grant.

In ordinary chat, the task performer handles activation for its current task.
When Orchestrator is active, activation is a master control action for one
identified live worker. The master handles it without dispatching a worker for
activation. Workers refer activation requests to the master.

Establish the current task, recipient, resources, and covered effects before
activation. If any of these are materially ambiguous, apply the shared
question rules in the boundary contract. Give the user a scoped notice before using the
grant. Apply the elevated rights contract to eligible actions, authorization
limits, and expiration.
