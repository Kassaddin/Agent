# Layout Migration, Protocol 2

Setup owns detection, explanation, and a read-only migration plan. Update owns
execution, recovery, structural verification, and the subsequent separate release
update. The trusted [migration helper](../scripts/migrate_kit.py) also travels in
Setup's generated bootstrap, so a user needs only the self-contained Setup package.
Bootstrap copies are generated from canonical sources, never maintained forks.

The transition is `.agent/` → `.agents/` and skill `context` → `project-context`.
The only migration target is `<project>/Agents`; the development checkout is not
an updater target. Read current boundaries, validate a published layout-2
baseline/receipt, and preserve local managed edits as conflicts. Preserve local
configuration, project-authored skills, context, checkpoints, and report evidence.
Known active path references are translated by the pinned transformation; report,
receipt, and old recovery bytes are retained. Host guidance integration is a
separate approved preview through [the integration helper](../scripts/integrate_project.py).

The plan lists every source/destination, before/after hash, content transformation,
and the exact policy relocation where applicable. Applying it requires actual
migration approval and the plan hash; an affected policy requires review of its
before/after values. Preflight read/create/modify/delete gates, directory gates,
links, baseline identity, and concurrent state before mutations. No Git operation
or downloaded migration script is run. Existing `.agents` content is a conflict.

The durable journal is `.agents/state/migration/layout-v3.json`. Progress is
`applying`, `recovery_required`, or `verified`. Recovery resumes only recorded
unchanged inputs or identifiable completed outputs and preserves uncertain or
concurrently edited files. Update is blocked while migration is incomplete.
Original bytes remain in the journal for bounded manual recovery; it is local
state excluded from releases. Recovery never discards unrelated content.

Migration verification establishes the canonical structure, not completion of a
release update or policy activation. A verified migration remains a separate
phase with the release update pending. Update re-verifies the original published
baseline and uses a deterministic relocated comparison view; it never invents a
new published identity or rewrites the captured original manifest/receipt merely
to make paths match. Normal release update/recovery then follows the
[Update contract](update-contract.md).
