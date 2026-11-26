# First Installation and Bootstrap Contract

Setup owns first installation and verified installation outcomes. For a legacy
kit it owns detection, explanation, and the migration plan. Update owns approved
migration execution/recovery and the later separate version update. Init owns
permissions and activation; host integration is a separate concrete approval.

The fixed source is `https://github.com/Kassaddin/Agents`, published packages only.
It applies to Setup alone; Update uses the release source configured for the
project, restricted to HTTPS GitHub sources.
The only fresh kit destination is `<project>/Agents`, using `.agents/` internally.
Require at least the core skills the Setup helper declares, including
`project-context` and `orchestrator`, layout 3/protocol 2, and kit guidance. Unknown sources, arbitrary occupied destinations,
or incompatible published assets stop the operation. Do not run candidate code.

The whole `setup/` folder is independently distributable. Its generated
`bootstrap/` contains owned verification/access/migration helpers and their
contracts; the release builder derives them from canonical sources. Python 3.10+
and PyYAML 6.x are prerequisites, not silently installed dependencies. There is
one maintained release protocol, not a Setup-specific fork. The self-contained
resources include the Update executor needed when the old updater cannot read
the new layout. Bootstrap payloads do not require installed sibling skills.

Fresh installation previews without writes, pins the tag/hash, preflights current
permissions, reserves the destination exclusively, journals file identities,
verifies every written file, and creates the initial Update receipt. Recovery
removes only identified unchanged Setup-created files when permitted, preserving
uncertain/concurrent content and leaving explicit recovery status. A pending
Setup journal blocks normal updates.

An older `.agent` kit first receives a published-baseline-backed migration plan.
Managed local edits or missing baseline evidence are explicit blockers. The plan
shows file mappings, content transformations, conflicts, policy relocation, and
the next separate update step. Approval and execution occur under the bundled
[Update migration contract](../bootstrap/update/references/migration-contract.md).
Setup never silently performs that migration or a release update on detection.

After verified installation, absent boundaries start the installed Init skill;
present boundaries mean ask whether to run it. Multiple candidates require a
selection. Installing files does not activate policy. Scope bootstrap approval
to the stated source/kit; it does not authorize general host traversal.

Project integration previews a small host AGENTS.md pointer and exact old kit-link
rewrites, obtains real approval, preserves unrelated bytes, and retains a backup.
The generated kit catalog routes requests to project-local skill instructions;
personal/global installation is separate and outside every kit workflow: a
user-performed copy of the complete release skills folder, which no kit skill
installs, updates, or verifies. A declined or blocked integration is
reported as pending, not silently treated as full project configuration.

Report installation, migration planning, activation, integration, and version
updating separately. Keep immutable JSON outcomes and reader Markdown together
through links. No publication or Git mutations are part of this flow.
